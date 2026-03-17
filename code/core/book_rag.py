#!/usr/bin/env python3
"""Shared utilities for building a local RAG system over this book."""

from __future__ import annotations

import json
import math
import os
import re
import textwrap
import urllib.error
import urllib.request
from collections import Counter
from pathlib import Path

from dotenv import load_dotenv

CORE_DIR = Path(__file__).resolve().parent
CODE_DIR = CORE_DIR.parent
PROJECT_DIR = CODE_DIR.parent
BUILD_DIR = CODE_DIR / "build"
load_dotenv(PROJECT_DIR / ".env")

OLLAMA_URL = os.getenv("OLLAMA_LOCAL_HOST", "http://127.0.0.1:11434")
OLLAMA_CLOUD_URL = os.getenv("OLLAMA_CLOUD_HOST", "https://ollama.com")
OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY", "")
CHAT_MODEL = "qwen3.5:2b"
EMBED_MODEL = "bge-m3:latest"
CORPUS_PATH = BUILD_DIR / "book_corpus.json"
INDEX_PATH = BUILD_DIR / "book_index.json"


def ensure_build_dir() -> None:
    BUILD_DIR.mkdir(parents=True, exist_ok=True)


def parse_quarto_chapters() -> list[Path]:
    config_path = PROJECT_DIR / "_quarto.yml"
    lines = config_path.read_text(encoding="utf-8").splitlines()
    chapters: list[Path] = []
    in_chapters = False
    for raw_line in lines:
        line = raw_line.rstrip()
        stripped = line.strip()
        if stripped == "chapters:":
            in_chapters = True
            continue
        if in_chapters:
            if re.match(r"^[A-Za-z]", line):
                break
            match = re.match(r"^\s*-\s+(.+\.qmd)\s*$", line)
            if match:
                path = PROJECT_DIR / match.group(1)
                if path.name != "references.qmd":
                    chapters.append(path)
    return chapters


def load_book_documents() -> list[dict[str, str]]:
    documents: list[dict[str, str]] = []
    for path in parse_quarto_chapters():
        text = path.read_text(encoding="utf-8")
        documents.append({"path": path.name, "text": text})
    return documents


def strip_quarto_noise(text: str) -> str:
    text = re.sub(r"^---\n.*?\n---\n", "", text, flags=re.DOTALL)
    text = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
    text = re.sub(r"\{\.unnumbered\}", "", text)
    return text


def chunk_document(path: str, text: str, target_chars: int = 1100) -> list[dict[str, str]]:
    cleaned = strip_quarto_noise(text)
    lines = cleaned.splitlines()
    chunks: list[dict[str, str]] = []
    heading_stack: list[str] = []
    buffer: list[str] = []

    def flush() -> None:
        nonlocal buffer
        body = "\n".join(line.strip() for line in buffer if line.strip()).strip()
        if not body:
            buffer = []
            return
        title = " > ".join(heading_stack) if heading_stack else Path(path).stem
        paragraphs = [part.strip() for part in re.split(r"\n\s*\n", body) if part.strip()]
        current = ""
        chunk_id = len(chunks) + 1
        for paragraph in paragraphs:
            candidate = paragraph if not current else f"{current}\n\n{paragraph}"
            if current and len(candidate) > target_chars:
                chunks.append(
                    {
                        "chunk_id": f"{Path(path).stem}-{chunk_id}",
                        "source_path": path,
                        "section": title,
                        "text": current.strip(),
                    }
                )
                chunk_id += 1
                current = paragraph
            else:
                current = candidate
        if current:
            chunks.append(
                {
                    "chunk_id": f"{Path(path).stem}-{chunk_id}",
                    "source_path": path,
                    "section": title,
                    "text": current.strip(),
                }
            )
        buffer = []

    for line in lines:
        heading_match = re.match(r"^(#{1,6})\s+(.*)$", line.strip())
        if heading_match:
            flush()
            level = len(heading_match.group(1))
            heading = heading_match.group(2).strip()
            heading_stack[:] = heading_stack[: level - 1]
            heading_stack.append(heading)
        else:
            buffer.append(line)
    flush()
    return chunks


def build_corpus() -> list[dict[str, str]]:
    corpus: list[dict[str, str]] = []
    for document in load_book_documents():
        corpus.extend(chunk_document(document["path"], document["text"]))
    return corpus


def save_json(path: Path, data: object) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def load_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def slugify_model_name(model_name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", model_name.lower()).strip("-")
    return slug or "model"


def index_path_for_model(embed_model: str) -> Path:
    return BUILD_DIR / f"book_index_{slugify_model_name(embed_model)}.json"


def is_cloud_model(model_name: str) -> bool:
    return model_name.endswith(":cloud") or model_name.endswith("-cloud")


def normalize_cloud_model_name(model_name: str) -> str:
    if model_name.endswith(":cloud"):
        return model_name[: -len(":cloud")]
    if model_name.endswith("-cloud"):
        return model_name[: -len("-cloud")]
    return model_name


def get_ollama_base_url(model_name: str | None = None) -> str:
    if model_name and is_cloud_model(model_name):
        return OLLAMA_CLOUD_URL
    return OLLAMA_URL


def get_ollama_headers(model_name: str | None = None, include_json: bool = True) -> dict[str, str]:
    headers: dict[str, str] = {}
    if include_json:
        headers["Content-Type"] = "application/json"
    if model_name and is_cloud_model(model_name):
        if not OLLAMA_API_KEY:
            raise RuntimeError(
                "Cloud model selected but OLLAMA_API_KEY is missing. "
                "Set it in the project's .env file."
            )
        headers["Authorization"] = f"Bearer {OLLAMA_API_KEY}"
    return headers


def ollama_post(endpoint: str, payload: dict, model_name: str | None = None) -> dict:
    request = urllib.request.Request(
        f"{get_ollama_base_url(model_name)}{endpoint}",
        data=json.dumps(payload).encode("utf-8"),
        headers=get_ollama_headers(model_name),
        method="POST",
    )
    with urllib.request.urlopen(request) as response:
        return json.loads(response.read().decode("utf-8"))


def ollama_get(endpoint: str, model_name: str | None = None) -> dict:
    request = urllib.request.Request(
        f"{get_ollama_base_url(model_name)}{endpoint}",
        headers=get_ollama_headers(model_name, include_json=False),
        method="GET",
    )
    with urllib.request.urlopen(request) as response:
        return json.loads(response.read().decode("utf-8"))


def list_ollama_models() -> list[str]:
    response = ollama_get("/api/tags")
    models = [item["name"] for item in response.get("models", []) if item.get("name")]
    return sorted(models)


def ollama_embed(texts: list[str], embed_model: str = EMBED_MODEL) -> list[list[float]]:
    model_name = normalize_cloud_model_name(embed_model) if is_cloud_model(embed_model) else embed_model
    response = ollama_post("/api/embed", {"model": model_name, "input": texts}, model_name=embed_model)
    return response["embeddings"]


def ollama_generate(prompt: str, chat_model: str = CHAT_MODEL) -> str:
    model_name = normalize_cloud_model_name(chat_model) if is_cloud_model(chat_model) else chat_model
    response = ollama_post(
        "/api/chat",
        {
            "model": model_name,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
            "options": {"temperature": 0.2},
        },
        model_name=chat_model,
    )
    message = response.get("message", {})
    return str(message.get("content", "")).strip()


def cosine_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    numerator = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = math.sqrt(sum(a * a for a in vec_a))
    norm_b = math.sqrt(sum(b * b for b in vec_b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return numerator / (norm_a * norm_b)


def tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9][a-z0-9\-\.]*", text.lower())


def sparse_scores(question: str, corpus: list[dict[str, str]]) -> dict[str, float]:
    tokenized_chunks = [tokenize(item["text"]) for item in corpus]
    query_tokens = tokenize(question)
    document_count = len(tokenized_chunks)
    avg_doc_len = sum(len(tokens) for tokens in tokenized_chunks) / max(document_count, 1)
    doc_freq = Counter()
    for tokens in tokenized_chunks:
        doc_freq.update(set(tokens))

    scores: dict[str, float] = {}
    k1 = 1.5
    b = 0.75
    for item, tokens in zip(corpus, tokenized_chunks):
        counts = Counter(tokens)
        score = 0.0
        for term in query_tokens:
            freq = counts[term]
            if freq == 0:
                continue
            idf = math.log(1 + (document_count - doc_freq[term] + 0.5) / (doc_freq[term] + 0.5))
            denom = freq + k1 * (1 - b + b * len(tokens) / max(avg_doc_len, 1))
            score += idf * (freq * (k1 + 1)) / denom
        scores[item["chunk_id"]] = score
    return scores


def min_max_normalize(scores: dict[str, float]) -> dict[str, float]:
    if not scores:
        return {}
    values = list(scores.values())
    low = min(values)
    high = max(values)
    if math.isclose(low, high):
        return {key: 1.0 for key in scores}
    return {key: (value - low) / (high - low) for key, value in scores.items()}


def dense_scores(question: str, index_data: dict, embed_model: str | None = None) -> dict[str, float]:
    model_name = embed_model or index_data.get("model", EMBED_MODEL)
    question_embedding = ollama_embed([question], embed_model=model_name)[0]
    scores: dict[str, float] = {}
    for item in index_data["chunks"]:
        scores[item["chunk_id"]] = cosine_similarity(question_embedding, item["embedding"])
    return scores


def hybrid_scores(question: str, corpus: list[dict[str, str]], index_data: dict, alpha: float = 0.65) -> dict[str, float]:
    dense = min_max_normalize(dense_scores(question, index_data))
    sparse = min_max_normalize(sparse_scores(question, corpus))
    all_ids = {item["chunk_id"] for item in corpus}
    return {
        chunk_id: alpha * dense.get(chunk_id, 0.0) + (1 - alpha) * sparse.get(chunk_id, 0.0)
        for chunk_id in all_ids
    }


def top_results(corpus: list[dict[str, str]], scores: dict[str, float], k: int) -> list[dict[str, str]]:
    items_by_id = {item["chunk_id"]: item for item in corpus}
    ranked = sorted(scores.items(), key=lambda item: item[1], reverse=True)[:k]
    results: list[dict[str, str]] = []
    for chunk_id, score in ranked:
        item = dict(items_by_id[chunk_id])
        item["score"] = score
        results.append(item)
    return results


def build_prompt(question: str, retrieved: list[dict[str, str]]) -> str:
    context = "\n\n".join(
        f"[{index}] {item['source_path']} | {item['section']} | score={item['score']:.3f}\n{item['text']}"
        for index, item in enumerate(retrieved, start=1)
    )
    return textwrap.dedent(
        f"""
        You are answering questions about the book project in the local workspace.
        Use only the retrieved context below.
        If the retrieved context is insufficient, say that clearly.
        Give a concise answer in English and finish with a line that starts with "Sources:".

        Question:
        {question}

        Retrieved context:
        {context}
        """
    ).strip()


def load_corpus() -> list[dict[str, str]]:
    return list(load_json(CORPUS_PATH))


def load_index() -> dict:
    return dict(load_json(INDEX_PATH))


def load_index_for_model(embed_model: str) -> dict:
    return dict(load_json(index_path_for_model(embed_model)))
