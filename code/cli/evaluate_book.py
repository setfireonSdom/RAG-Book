#!/usr/bin/env python3
"""Evaluate the book QA pipeline with a small local question set."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).parent
CODE_DIR = BASE_DIR.parent
QUESTIONS_PATH = CODE_DIR / "data" / "book_eval_questions.json"
RUNNER_PATH = BASE_DIR / "ask_book.py"


def run_question(question: str, chat_model: str, embed_model: str) -> str:
    cmd = [
        "python3",
        str(RUNNER_PATH),
        "--question",
        question,
        "--chat-model",
        chat_model,
        "--embed-model",
        embed_model,
    ]
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        error_text = result.stderr.strip() or result.stdout.strip() or f"Exit code {result.returncode}"
        raise RuntimeError(
            "Evaluation failed while running ask_book.py.\n"
            f"Question: {question}\n"
            f"Command: {' '.join(cmd)}\n"
            f"Error: {error_text}"
        )
    return result.stdout


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate the book QA pipeline.")
    parser.add_argument("--chat-model", default="qwen3.5:2b")
    parser.add_argument("--embed-model", default="bge-m3:latest")
    args = parser.parse_args()

    items = json.loads(QUESTIONS_PATH.read_text(encoding="utf-8"))
    retrieval_hits = 0
    answer_hits = 0

    for item in items:
        output = run_question(item["question"], chat_model=args.chat_model, embed_model=args.embed_model)
        retrieved_ok = item["expected_source_path"] in output
        answer_ok = all(keyword.lower() in output.lower() for keyword in item["expected_keywords"])
        retrieval_hits += int(retrieved_ok)
        answer_hits += int(answer_ok)

        print("\n=== Evaluation Case ===")
        print(f"Question: {item['question']}")
        print(f"Retrieved expected chapter: {'yes' if retrieved_ok else 'no'}")
        print(f"Answer contains expected concepts: {'yes' if answer_ok else 'no'}")

    total = len(items)
    print("\n=== Summary ===")
    print(f"Chat model: {args.chat_model}")
    print(f"Embedding model: {args.embed_model}")
    print(f"Retrieval hit rate: {retrieval_hits}/{total}")
    print(f"Answer concept hit rate: {answer_hits}/{total}")


if __name__ == "__main__":
    main()
