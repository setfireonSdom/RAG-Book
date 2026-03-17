#!/usr/bin/env python3
"""Embed the chunked book corpus and store a local JSON index."""

from __future__ import annotations

import argparse
import sys
import urllib.error
from pathlib import Path

CODE_DIR = Path(__file__).resolve().parents[1]
if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))

from core.book_rag import CORPUS_PATH, EMBED_MODEL, ensure_build_dir, index_path_for_model, load_corpus, ollama_embed, save_json


def main() -> None:
    parser = argparse.ArgumentParser(description="Build an embedding index for the book corpus.")
    parser.add_argument("--embed-model", default=EMBED_MODEL)
    args = parser.parse_args()

    ensure_build_dir()
    if not CORPUS_PATH.exists():
        raise SystemExit("Missing book corpus. Run `python3 code/cli/ingest_book.py` first.")

    corpus = load_corpus()
    texts = [item["text"] for item in corpus]
    embed_model = args.embed_model
    index_path = index_path_for_model(embed_model)
    try:
        embeddings = ollama_embed(texts, embed_model=embed_model)
    except urllib.error.URLError as exc:
        raise SystemExit(
            "Could not reach Ollama at http://127.0.0.1:11434. "
            f"Make sure the Ollama app or `ollama serve` is running and that {embed_model} is pulled."
        ) from exc

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

    save_json(index_path, {"model": embed_model, "chunks": indexed_chunks})
    print(f"Wrote {len(indexed_chunks)} embedded chunks to {index_path}")


if __name__ == "__main__":
    main()
