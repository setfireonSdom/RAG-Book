#!/usr/bin/env python3
"""Compare dense, sparse, and hybrid retrieval on the book corpus."""

from __future__ import annotations

import argparse
import sys
import urllib.error
from pathlib import Path

CODE_DIR = Path(__file__).resolve().parents[1]
if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))

from core.book_rag import (
    CORPUS_PATH,
    EMBED_MODEL,
    dense_scores,
    hybrid_scores,
    load_corpus,
    load_index_for_model,
    index_path_for_model,
    sparse_scores,
    top_results,
)


def print_method(name: str, results: list[dict[str, str]]) -> None:
    print(f"\n=== {name} ===")
    for rank, item in enumerate(results, start=1):
        print(f"\n[{rank}] {item['source_path']} | {item['section']} | score={item['score']:.3f}")
        print(item["text"])


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare retrieval methods on the book corpus.")
    parser.add_argument("--question", default="How does the book compare RAG with fine-tuning?")
    parser.add_argument("--top-k", type=int, default=3)
    parser.add_argument("--alpha", type=float, default=0.6, help="Dense weight in hybrid scoring.")
    parser.add_argument("--embed-model", default=EMBED_MODEL)
    args = parser.parse_args()

    if not CORPUS_PATH.exists():
        raise SystemExit("Missing book corpus. Run `python3 code/cli/ingest_book.py` first.")
    index_path = index_path_for_model(args.embed_model)
    if not index_path.exists():
        raise SystemExit(f"Missing book index for {args.embed_model}. Build it first.")

    corpus = load_corpus()
    index_data = load_index_for_model(args.embed_model)
    try:
        dense = top_results(corpus, dense_scores(args.question, index_data), args.top_k)
        sparse = top_results(corpus, sparse_scores(args.question, corpus), args.top_k)
        hybrid = top_results(corpus, hybrid_scores(args.question, corpus, index_data, args.alpha), args.top_k)
    except urllib.error.URLError as exc:
        raise SystemExit(
            "Could not reach Ollama at http://127.0.0.1:11434. "
            f"Start Ollama first and make sure {EMBED_MODEL} is available."
        ) from exc

    print(f"Question: {args.question}")
    print_method("Dense Retrieval", dense)
    print_method("Sparse Retrieval", sparse)
    print_method("Hybrid Retrieval", hybrid)


if __name__ == "__main__":
    main()
