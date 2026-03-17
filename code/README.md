# Local Book QA Project

This folder contains a small local RAG project built around the actual Quarto source of this book.

## Structure

- `code/app/`
  Streamlit UI entrypoint.
- `code/cli/`
  Command-line entrypoints for ingestion, indexing, asking questions, retrieval comparison, and evaluation.
- `code/core/`
  Shared RAG logic used by both the UI and the CLI tools.
- `code/data/`
  Evaluation fixtures.
- `code/build/`
  Generated corpus and index artifacts.

## Install

```bash
pip install -r requirements.txt
```

## Environment

This project now reads Ollama settings from the root `.env` file.

For local models, the default local host is already configured:

```dotenv
OLLAMA_LOCAL_HOST=http://127.0.0.1:11434
```

For Ollama cloud/remote models, add your API key:

```dotenv
OLLAMA_CLOUD_HOST=https://ollama.com
OLLAMA_API_KEY=your_ollama_api_key_here
```

## Models

The default local setup uses:

```bash
ollama pull qwen3.5:2b
ollama pull bge-m3:latest
```

The chat layer can also use Ollama cloud models that appear in `ollama list`, as long as `OLLAMA_API_KEY` is set in `.env`.

## Workflow

1. `ingest_book.py`
   Reads the book's `.qmd` files listed in `_quarto.yml`, removes Quarto noise, and writes chunked text to `code/build/book_corpus.json`.
2. `build_book_index.py`
   Embeds those chunks with the selected embedding model and stores the result in `code/build/`.
3. `ask_book.py`
   Uses hybrid retrieval plus the selected chat model to answer questions about the book and prints the retrieved passages.
4. `evaluate_book.py`
   Runs a small repeatable evaluation set against the live pipeline.
5. `retrieval_compare.py`
   Compares dense, sparse, and hybrid retrieval over the same book corpus.
6. `chat_app.py`
   Starts a lightweight Streamlit chat UI over the same pipeline, with selectable Ollama chat and embedding models.

## Run

```bash
python3 code/cli/ingest_book.py
python3 code/cli/build_book_index.py --embed-model bge-m3:latest
python3 code/cli/ask_book.py --question "When should RAG be preferred over fine-tuning?" --chat-model qwen3.5:2b --embed-model bge-m3:latest
python3 code/cli/retrieval_compare.py --question "How does the book compare RAG with fine-tuning?" --embed-model bge-m3:latest
python3 code/cli/evaluate_book.py --chat-model qwen3.5:2b --embed-model bge-m3:latest
streamlit run code/app/chat_app.py
```

In the chat UI, you can choose different Ollama models, including remote/cloud-backed ones shown by `ollama list`. If you choose a cloud model, make sure `OLLAMA_API_KEY` is filled in inside `.env`. If you change the embedding model, build a fresh index for that model from the sidebar first.

The page app lives at `code/app/chat_app.py`, and it calls the shared pipeline in `code/core/book_rag.py`.
