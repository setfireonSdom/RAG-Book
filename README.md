# RAG Book

A practical book project about Retrieval-Augmented Generation (RAG), paired with a runnable local RAG system built over the book itself.

This repository combines three things:

- the Quarto source of the book;
- a runnable RAG codebase under `code/`;
- a publishable static site under `docs/` for GitHub Pages.

## What This Project Includes

### Book

The book is written in Quarto and covers:

- RAG fundamentals;
- data preparation;
- embeddings and indexing;
- retrieval optimization;
- generation integration;
- evaluation;
- advanced RAG architectures.

### Code

The codebase turns the book's own `.qmd` files into a retrieval corpus and provides:

- corpus ingestion;
- embedding and indexing;
- dense, sparse, and hybrid retrieval;
- a CLI question-answering workflow;
- a Streamlit chat UI;
- local and Ollama cloud model support.

### Docs Site

The `docs/` folder contains the rendered book site for GitHub Pages.

## Repository Structure

```text
.
├── *.qmd
├── _quarto.yml
├── code/
│   ├── app/
│   ├── cli/
│   ├── core/
│   ├── data/
│   └── build/
├── docs/
├── requirements.txt
├── CURRENT_SYSTEM_GUIDE.md
└── PROJECT_ROADMAP.md
```

## Local Setup

Install dependencies:

```bash
pip install -r requirements.txt
```

If using local Ollama models:

```bash
ollama pull qwen3.5:2b
ollama pull bge-m3:latest
```

If using Ollama cloud models, fill in `.env` using `.env.example`.

## Run The RAG System

Build the corpus:

```bash
python3 code/cli/ingest_book.py
```

Build the embedding index:

```bash
python3 code/cli/build_book_index.py --embed-model bge-m3:latest
```

Ask a question:

```bash
python3 code/cli/ask_book.py --question "When should RAG be preferred over fine-tuning?" --chat-model qwen3.5:2b --embed-model bge-m3:latest
```

Start the chat UI:

```bash
streamlit run code/app/chat_app.py
```

## Build And Publish The Book

The Quarto source stays in the repository root.

After rendering the book locally, copy the contents of `_book/` into `docs/`. GitHub Pages should publish from `docs/`.

## Helpful Project Notes

- [CURRENT_SYSTEM_GUIDE.md](/Users/yummmy/Downloads/book/RAG_Book/RAG%20Book/CURRENT_SYSTEM_GUIDE.md)
  Explains how the current codebase works.
- [PROJECT_ROADMAP.md](/Users/yummmy/Downloads/book/RAG_Book/RAG%20Book/PROJECT_ROADMAP.md)
  Describes the recommended next stages for the project.

## Project Goal

This is both a learning project and a portfolio project.

The long-term goal is to use the book and the code together to build strong practical understanding of RAG, then grow the system from a teaching-oriented baseline into a more engineering-grade implementation.
