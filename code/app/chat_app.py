#!/usr/bin/env python3
"""A tiny Streamlit chat UI for the local book QA pipeline."""

from __future__ import annotations

import sys
import urllib.error
from pathlib import Path

import streamlit as st

CODE_DIR = Path(__file__).resolve().parents[1]
if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))

from core.book_rag import (
    CHAT_MODEL,
    CORPUS_PATH,
    EMBED_MODEL,
    build_corpus,
    build_prompt,
    ensure_build_dir,
    hybrid_scores,
    index_path_for_model,
    load_corpus,
    load_index_for_model,
    list_ollama_models,
    ollama_embed,
    ollama_generate,
    save_json,
    top_results,
)

st.set_page_config(page_title="RAG Book Chat", layout="wide")


def build_corpus_file() -> str:
    ensure_build_dir()
    corpus = build_corpus()
    save_json(CORPUS_PATH, corpus)
    return f"Built corpus with {len(corpus)} chunks."


def build_index_file(embed_model: str) -> str:
    ensure_build_dir()
    if not CORPUS_PATH.exists():
        raise RuntimeError("Corpus missing. Build the corpus first.")
    corpus = load_corpus()
    texts = [item["text"] for item in corpus]
    embeddings = ollama_embed(texts, embed_model=embed_model)
    indexed_chunks = []
    for item, embedding in zip(corpus, embeddings):
        indexed_chunks.append(
            {
                "chunk_id": item["chunk_id"],
                "source_path": item["source_path"],
                "section": item["section"],
                "text": item["text"],
                "embedding": embedding,
            }
        )
    index_path = index_path_for_model(embed_model)
    save_json(index_path, {"model": embed_model, "chunks": indexed_chunks})
    return f"Built index with {len(indexed_chunks)} embedded chunks for {embed_model}."


def answer_question(question: str, top_k: int, alpha: float, chat_model: str, embed_model: str) -> tuple[str, list[dict[str, str]]]:
    if not CORPUS_PATH.exists():
        raise RuntimeError("Corpus missing. Build the corpus first.")
    index_path = index_path_for_model(embed_model)
    if not index_path.exists():
        raise RuntimeError(f"Index missing for {embed_model}. Build that index first.")

    corpus = load_corpus()
    index_data = load_index_for_model(embed_model)
    retrieved = top_results(corpus, hybrid_scores(question, corpus, index_data, alpha), top_k)
    prompt = build_prompt(question, retrieved)
    answer = ollama_generate(prompt, chat_model=chat_model)
    return answer, retrieved


if "messages" not in st.session_state:
    st.session_state.messages = []

try:
    available_models = list_ollama_models()
except urllib.error.URLError:
    available_models = []

default_chat_model = CHAT_MODEL if CHAT_MODEL in available_models else (available_models[0] if available_models else CHAT_MODEL)
default_embed_model = EMBED_MODEL if EMBED_MODEL in available_models else (available_models[0] if available_models else EMBED_MODEL)

st.title("RAG Book Chat")
st.caption("Local QA over this book with selectable Ollama models")

with st.sidebar:
    st.subheader("Models")
    if available_models:
        chat_model = st.selectbox(
            "Chat Model",
            options=available_models,
            index=available_models.index(default_chat_model),
            help="You can choose local or Ollama remote/cloud models here.",
        )
        embed_model = st.selectbox(
            "Embedding Model",
            options=available_models,
            index=available_models.index(default_embed_model),
            help="Changing the embedding model requires rebuilding the index for that model.",
        )
    else:
        st.warning("Could not load model list from Ollama yet.")
        chat_model = CHAT_MODEL
        embed_model = EMBED_MODEL

    st.subheader("Build Pipeline")
    st.write("Prepare the book corpus and embedding index before chatting.")

    if st.button("1. Build Corpus", use_container_width=True):
        try:
            with st.spinner("Chunking book chapters..."):
                message = build_corpus_file()
            st.success(message)
        except Exception as exc:  # noqa: BLE001
            st.error(str(exc))

    if st.button("2. Build Index", use_container_width=True):
        try:
            with st.spinner("Embedding chunks with Ollama..."):
                message = build_index_file(embed_model)
            st.success(message)
        except urllib.error.URLError:
            st.error(
                "Could not reach Ollama at http://127.0.0.1:11434. "
                "Make sure the Ollama app is open or run `ollama serve` in a terminal."
            )
        except RuntimeError as exc:
            st.error(str(exc))
        except Exception as exc:  # noqa: BLE001
            st.error(str(exc))

    st.subheader("Retrieval Settings")
    top_k = st.slider("Top K", min_value=2, max_value=8, value=4, step=1)
    alpha = st.slider("Dense Weight", min_value=0.0, max_value=1.0, value=0.65, step=0.05)

    st.subheader("Status")
    st.write(f"Corpus ready: {'yes' if CORPUS_PATH.exists() else 'no'}")
    st.write(f"Index ready for `{embed_model}`: {'yes' if index_path_for_model(embed_model).exists() else 'no'}")

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message.get("sources"):
            with st.expander("Retrieved Context", expanded=False):
                for item in message["sources"]:
                    st.markdown(
                        f"**{item['source_path']}**  \n"
                        f"{item['section']}  \n"
                        f"`score={item['score']:.3f}`"
                    )
                    st.write(item["text"])

question = st.chat_input("Ask a question about this book...")

if question:
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        try:
            with st.spinner("Retrieving chapters and generating an answer..."):
                answer, sources = answer_question(
                    question,
                    top_k=top_k,
                    alpha=alpha,
                    chat_model=chat_model,
                    embed_model=embed_model,
                )
            st.markdown(answer)
            with st.expander("Retrieved Context", expanded=False):
                for item in sources:
                    st.markdown(
                        f"**{item['source_path']}**  \n"
                        f"{item['section']}  \n"
                        f"`score={item['score']:.3f}`"
                    )
                    st.write(item["text"])
            st.session_state.messages.append(
                {"role": "assistant", "content": answer, "sources": sources}
            )
        except urllib.error.URLError:
            st.error(
                "Could not reach Ollama at http://127.0.0.1:11434. "
                "Make sure the Ollama app is open or run `ollama serve` in a terminal."
            )
        except RuntimeError as exc:
            st.error(str(exc))
        except Exception as exc:  # noqa: BLE001
            st.error(str(exc))
