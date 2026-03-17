# Current System Guide

This document explains the current code system in this repository:

- what each file does;
- how the files connect to one another;
- what the main data flow looks like;
- how to use the system in practice.

The goal is to make the current project easy to understand before adding more advanced upgrades.

## 1. What This System Is

The current implementation is a teaching-oriented but fully runnable RAG system built around the book itself.

Instead of using an external demo dataset, the project turns the book's own Quarto source files into a retrieval corpus.

That means the system does this:

1. read the book's `.qmd` files;
2. chunk the text into retrieval units;
3. embed those chunks;
4. store an index;
5. retrieve relevant chunks for a question;
6. send the retrieved context to an Ollama chat model;
7. return an answer with visible retrieved context.

So this project is not just "about RAG." It is itself a RAG system over the book.

## 2. High-Level Structure

The code is organized into five main areas:

```text
code/
  app/
  cli/
  core/
  data/
  build/
```

Their roles are:

- `code/app/`
  User-facing app entrypoints.
- `code/cli/`
  Command-line tools you run directly.
- `code/core/`
  Shared core logic used by both the app and CLI.
- `code/data/`
  Input data for evaluation.
- `code/build/`
  Generated artifacts such as the chunked corpus and embedding indexes.

## 3. The Most Important File

The central file in the current system is:

- [code/core/book_rag.py](/Users/yummmy/Downloads/book/RAG_Book/RAG%20Book/code/core/book_rag.py)

This is the shared backend logic.

Almost everything important flows through it:

- reading the Quarto book structure;
- loading chapter files;
- cleaning and chunking documents;
- calling Ollama;
- computing dense and sparse retrieval signals;
- combining them with hybrid retrieval;
- building prompts;
- loading and saving corpus/index data.

If you only read one code file to understand the project, start here.

## 4. File-by-File Explanation

### 4.1 App Layer

- [code/app/chat_app.py](/Users/yummmy/Downloads/book/RAG_Book/RAG%20Book/code/app/chat_app.py)

This is the Streamlit web UI.

What it does:

- shows the chat interface;
- lets you choose the chat model and embedding model;
- provides buttons for `Build Corpus` and `Build Index`;
- sends questions into the backend pipeline;
- shows the answer;
- shows the retrieved context used to answer.

What it does not do:

- it does not implement chunking logic itself;
- it does not implement retrieval logic itself;
- it does not implement Ollama communication itself.

Instead, it imports those capabilities from `code/core/book_rag.py`.

So you can think of `chat_app.py` as the UI wrapper around the shared RAG pipeline.

### 4.2 CLI Layer

- [code/cli/ingest_book.py](/Users/yummmy/Downloads/book/RAG_Book/RAG%20Book/code/cli/ingest_book.py)

This script builds the corpus.

What it does:

- reads the book source files;
- chunks them;
- writes the result to `code/build/book_corpus.json`.

Use it when:

- the book content changed;
- chunking logic changed;
- you want to rebuild the corpus from source.

---

- [code/cli/build_book_index.py](/Users/yummmy/Downloads/book/RAG_Book/RAG%20Book/code/cli/build_book_index.py)

This script builds the embedding index.

What it does:

- loads `code/build/book_corpus.json`;
- calls the selected embedding model through Ollama;
- stores chunk embeddings in an index file under `code/build/`.

Use it when:

- you built or rebuilt the corpus;
- you changed the embedding model;
- you need a fresh retrieval index.

---

- [code/cli/ask_book.py](/Users/yummmy/Downloads/book/RAG_Book/RAG%20Book/code/cli/ask_book.py)

This is the command-line question-answering tool.

What it does:

- loads the corpus;
- loads the index for the selected embedding model;
- computes hybrid retrieval scores;
- selects the top chunks;
- builds a prompt;
- sends the prompt to the selected chat model;
- prints the answer and retrieved context.

Use it when:

- you want to test the pipeline quickly without the web UI;
- you want reproducible CLI-based runs;
- you want to inspect retrieval behavior directly.

---

- [code/cli/retrieval_compare.py](/Users/yummmy/Downloads/book/RAG_Book/RAG%20Book/code/cli/retrieval_compare.py)

This script is for retrieval analysis, not for normal end-user answering.

What it does:

- runs dense retrieval;
- runs sparse retrieval;
- runs hybrid retrieval;
- prints the top results from each method.

Use it when:

- you want to understand retrieval quality;
- you want to compare retrieval strategies;
- you want to debug why a question is or is not finding the right chunks.

---

- [code/cli/evaluate_book.py](/Users/yummmy/Downloads/book/RAG_Book/RAG%20Book/code/cli/evaluate_book.py)

This is the lightweight evaluation script.

What it does:

- reads the evaluation questions from `code/data/book_eval_questions.json`;
- runs the CLI question-answering path;
- checks whether expected source files and expected concepts appear in the output;
- prints a small summary.

Use it when:

- you want a repeatable sanity-check for the current system;
- you changed retrieval or prompting and want to see whether basic quality regressed.

### 4.3 Core Layer

- [code/core/book_rag.py](/Users/yummmy/Downloads/book/RAG_Book/RAG%20Book/code/core/book_rag.py)

This file contains the actual shared mechanics of the project.

The most important functions and what they do:

- `parse_quarto_chapters()`
  Reads `_quarto.yml` and determines which `.qmd` files are part of the book corpus.

- `load_book_documents()`
  Reads the actual chapter files.

- `strip_quarto_noise()`
  Removes some Quarto-specific formatting noise before chunking.

- `chunk_document()`
  Turns a chapter into smaller retrieval chunks.

- `build_corpus()`
  Runs the full chapter-to-chunk process across the book.

- `ollama_embed()`
  Calls Ollama to create embeddings.

- `ollama_generate()`
  Calls Ollama to generate answers.

- `sparse_scores()`
  Computes a simple BM25-style sparse retrieval score.

- `dense_scores()`
  Computes dense retrieval scores using embeddings.

- `hybrid_scores()`
  Combines dense and sparse retrieval into a single ranking.

- `top_results()`
  Selects the highest-scoring chunks.

- `build_prompt()`
  Formats retrieved context and the user question into a prompt for the model.

This file is the system brain. The app and CLI both depend on it.

### 4.4 Data Layer

- [code/data/book_eval_questions.json](/Users/yummmy/Downloads/book/RAG_Book/RAG%20Book/code/data/book_eval_questions.json)

This file contains evaluation cases.

Each item includes:

- a question;
- expected keywords or concepts;
- an expected source file.

It is used by `code/cli/evaluate_book.py`.

### 4.5 Build Layer

- [code/build/book_corpus.json](/Users/yummmy/Downloads/book/RAG_Book/RAG%20Book/code/build/book_corpus.json)

This is the chunked corpus generated from the `.qmd` files.

It is an intermediate artifact.

You do not edit it manually. It is produced by `code/cli/ingest_book.py`.

---

- files like `code/build/book_index_*.json`

These are embedding indexes.

They are produced by `code/cli/build_book_index.py`.

They depend on the embedding model. Different embedding models should have separate index files.

## 5. How the Pieces Connect

### 5.1 Main Pipeline

The full pipeline looks like this:

```text
_quarto.yml
  -> chapter .qmd files
  -> ingest_book.py
  -> code/core/book_rag.py
  -> code/build/book_corpus.json
  -> build_book_index.py
  -> code/build/book_index_*.json
  -> ask_book.py or chat_app.py
  -> retrieved chunks
  -> Ollama chat model
  -> answer
```

### 5.2 App Call Flow

The app flow is:

```text
chat_app.py
  -> build_corpus_file()
     -> book_rag.build_corpus()
     -> save code/build/book_corpus.json

  -> build_index_file()
     -> book_rag.ollama_embed()
     -> save code/build/book_index_*.json

  -> answer_question()
     -> load corpus
     -> load index
     -> hybrid retrieval
     -> build prompt
     -> ollama_generate()
     -> return answer + sources
```

### 5.3 CLI Call Flow

The CLI tools do the same core operations, but separately:

- `ingest_book.py`
  builds the corpus
- `build_book_index.py`
  builds the index
- `ask_book.py`
  runs question-answering
- `retrieval_compare.py`
  analyzes retrieval behavior
- `evaluate_book.py`
  evaluates the QA path

So the CLI is useful for understanding and debugging each stage in isolation.

## 6. Model Behavior

The system supports both:

- local Ollama models;
- Ollama cloud models.

How it decides:

- local models use the local Ollama host from `.env`;
- cloud models use the cloud host and require `OLLAMA_API_KEY`.

This means:

- generation can be local or cloud;
- embeddings are usually best kept on a local embedding model such as `bge-m3:latest`;
- if you change the embedding model, you should rebuild the index.

## 7. How to Use the System

### 7.1 One-Time Setup

Install dependencies:

```bash
pip install -r requirements.txt
```

If using local models:

```bash
ollama pull qwen3.5:2b
ollama pull bge-m3:latest
```

If using cloud models:

- fill in `OLLAMA_API_KEY` inside `.env`

### 7.2 CLI Workflow

Build the corpus:

```bash
python3 code/cli/ingest_book.py
```

Build the index:

```bash
python3 code/cli/build_book_index.py --embed-model bge-m3:latest
```

Ask a question:

```bash
python3 code/cli/ask_book.py \
  --question "When should RAG be preferred over fine-tuning?" \
  --chat-model qwen3.5:2b \
  --embed-model bge-m3:latest
```

Compare retrieval methods:

```bash
python3 code/cli/retrieval_compare.py \
  --question "How does the book compare RAG with fine-tuning?" \
  --embed-model bge-m3:latest
```

Run evaluation:

```bash
python3 code/cli/evaluate_book.py
```

### 7.3 App Workflow

Start the app:

```bash
streamlit run code/app/chat_app.py
```

Then:

1. choose the chat model;
2. choose the embedding model;
3. click `Build Corpus`;
4. click `Build Index`;
5. ask questions in the chat input.

### 7.4 When to Rebuild Things

Rebuild the corpus if:

- the book `.qmd` files changed;
- chunking logic changed;
- book structure changed.

Rebuild the index if:

- the corpus changed;
- the embedding model changed;
- the index format changed.

You do not need to rebuild the index just because the chat model changed.

## 8. What This System Is Good At

The current system is especially good for:

- learning the structure of a RAG pipeline;
- seeing how retrieval and generation interact;
- experimenting with local and cloud model choices;
- using the book itself as a living knowledge base;
- building confidence before moving to more advanced systems.

## 9. What This System Does Not Yet Have

The current system is still a baseline.

It does not yet include:

- a standard vector database such as FAISS, Milvus, or Qdrant;
- more advanced chunking and metadata pipelines;
- reranking;
- richer evaluation frameworks;
- production-style observability.

That is expected. This version is the foundation that later upgrades will build on.

## 10. The Best Way to Study It

A good reading order for understanding the code is:

1. `code/core/book_rag.py`
2. `code/cli/ingest_book.py`
3. `code/cli/build_book_index.py`
4. `code/cli/ask_book.py`
5. `code/app/chat_app.py`
6. `code/cli/retrieval_compare.py`
7. `code/cli/evaluate_book.py`

That order usually makes the system click much faster than reading the files randomly.
