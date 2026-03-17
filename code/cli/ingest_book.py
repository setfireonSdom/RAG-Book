#!/usr/bin/env python3
"""Extract chunked book content from the Quarto source files."""

from __future__ import annotations

import sys
from pathlib import Path

CODE_DIR = Path(__file__).resolve().parents[1]
if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))

from core.book_rag import CORPUS_PATH, build_corpus, ensure_build_dir, save_json


def main() -> None:
    ensure_build_dir()
    corpus = build_corpus()
    save_json(CORPUS_PATH, corpus)
    print(f"Wrote {len(corpus)} chunks to {CORPUS_PATH}")


if __name__ == "__main__":
    main()
