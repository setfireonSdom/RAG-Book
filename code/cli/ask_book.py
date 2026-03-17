#!/usr/bin/env python3
"""Ask questions against the book using a local hybrid retriever and Ollama."""

from __future__ import annotations

import argparse
import sys
import urllib.error
from pathlib import Path

CODE_DIR = Path(__file__).resolve().parents[1]
if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))

from core.book_rag import (
    CHAT_MODEL,
    CORPUS_PATH,
    build_prompt,
    hybrid_scores,
    load_corpus,
    load_index_for_model,
    index_path_for_model,
    ollama_generate,
    top_results,
    EMBED_MODEL,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Ask a question about this book.")
    parser.add_argument("--question", required=True)
    parser.add_argument("--top-k", type=int, default=4)
    parser.add_argument("--alpha", type=float, default=0.65, help="Dense weight in hybrid retrieval.")
    parser.add_argument("--chat-model", default=CHAT_MODEL)
    parser.add_argument("--embed-model", default=EMBED_MODEL)
    args = parser.parse_args()

    if not CORPUS_PATH.exists():
        raise SystemExit("Missing book corpus. Run `python3 code/cli/ingest_book.py` first.")
    index_path = index_path_for_model(args.embed_model)
    if not index_path.exists():
        raise SystemExit(
            f"Missing book index for {args.embed_model}. "
            "Build it first from the UI or create it with a matching index build step."
        )

    corpus = load_corpus()
    index_data = load_index_for_model(args.embed_model)

    try:
        results = top_results(corpus, hybrid_scores(args.question, corpus, index_data, args.alpha), args.top_k)
        prompt = build_prompt(args.question, results)
        answer = ollama_generate(prompt, chat_model=args.chat_model)
    except urllib.error.URLError as exc:
        raise SystemExit(
            "Could not reach Ollama at http://127.0.0.1:11434. "
            f"Make sure the Ollama app or `ollama serve` is running and that {args.chat_model} is pulled."
        ) from exc

    print("\n=== Question ===")
    print(args.question)
    print("\n=== Retrieved Context ===")
    for index, item in enumerate(results, start=1):
        print(f"\n[{index}] {item['source_path']} | {item['section']} | score={item['score']:.3f}")
        print(item["text"])
    print("\n=== Answer ===")
    print(answer)


if __name__ == "__main__":
    main()
