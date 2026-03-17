# Project Roadmap

This file is a reminder for what this project is now, why it matters, and what to do next after the current version is fully understood.

## Current Stage

The project is already a real, runnable RAG system, but it is still a teaching-oriented baseline rather than a full engineering-grade RAG stack.

What the current version already has:

- a real corpus built from the book's own `.qmd` files;
- corpus ingestion and chunking;
- embedding generation through Ollama;
- dense retrieval, sparse retrieval, and hybrid retrieval;
- a command-line workflow;
- a Streamlit chat interface;
- local-model and Ollama cloud-model support for generation;
- a small evaluation script.

What this version is best for:

- understanding how a RAG pipeline works end to end;
- learning the relationship between corpus, chunking, retrieval, prompting, and generation;
- building intuition before adding more infrastructure;
- creating a solid "first serious RAG project" foundation.

## First Goal

Before adding more complexity, make sure the current system is fully understood.

The minimum understanding checklist:

- explain how `_quarto.yml` determines which `.qmd` files become the corpus;
- explain how chunks are produced and stored in `code/build/book_corpus.json`;
- explain how embeddings are created and why indexes depend on the embedding model;
- explain the difference between dense, sparse, and hybrid retrieval in this codebase;
- explain how the Streamlit app calls the shared pipeline;
- explain the difference between local Ollama calls and Ollama cloud model calls;
- explain what the evaluation script measures and what it does not measure.

If all of that can be explained clearly, the baseline project is genuinely understood.

## Why This Matters

The purpose of this project is not only to build a demo. The deeper goal is to use the book and the project together to master RAG well enough for real work and job interviews.

That means the final outcome should become:

- a book that teaches RAG clearly;
- a repository that demonstrates practical RAG implementation;
- a project story that can be explained in interviews;
- a learning path that moves from baseline implementation to engineering-grade systems.

## Next Major Upgrade

The next best upgrade is to add a FAISS-based vector index.

Why FAISS should come next:

- it is a standard technology in RAG education and engineering;
- it upgrades the current project from a baseline JSON similarity setup to a more realistic vector-search system;
- it fits naturally with Chapter 3 of the book;
- it makes the project stronger as a portfolio piece.

The key idea is not to replace the current system completely. Instead:

- keep the current version as the "baseline implementation";
- add a second implementation as the "FAISS implementation";
- compare them in both the codebase and the book.

## Recommended Development Order

### Phase 1: Master the Current Baseline

Do this first:

1. read the current code until the full flow is easy to explain;
2. use the chat app and CLI tools to test many questions;
3. inspect weak answers and trace them back to chunking, retrieval, or prompting;
4. improve the book where the system reveals unclear explanations;
5. add more evaluation questions to `code/data/book_eval_questions.json`.

### Phase 2: Add FAISS

Planned work:

1. create a FAISS-based indexing module;
2. create a FAISS-based asking workflow;
3. keep the same corpus and embedding pipeline where possible;
4. compare the current baseline retrieval path with the FAISS path;
5. update Chapter 3 so the book matches the implementation.

Suggested future structure:

```text
code/
  app/
  cli/
  core/
  data/
  build/
  faiss/
```

The baseline path should remain understandable. The FAISS path should be introduced as an engineering upgrade, not as a replacement for learning the basics.

### Phase 3: Improve Retrieval Quality

After FAISS, the next useful upgrades are:

1. metadata filtering;
2. better chunking strategies;
3. reranking;
4. retrieval diagnostics and logging;
5. more robust evaluation.

These changes should be reflected in the book as practical system improvements rather than isolated tricks.

### Phase 4: Make It Job-Ready

At that point, the project should be polished into something presentable:

1. clean repository structure;
2. strong README and setup instructions;
3. clear explanation of baseline vs engineering version;
4. reproducible examples;
5. better evaluation coverage;
6. well-written chapters that mirror the codebase.

The final interview-ready story should sound something like this:

"I built a RAG system over a real corpus derived from a book project. I started with a minimal baseline to understand the mechanics, then upgraded it with more realistic indexing and retrieval techniques, evaluation, and a usable interface. I wrote the book and the code together so the theory and implementation stayed aligned."

## Practical Reminder

Do not rush into too many new tools at once.

The healthiest sequence is:

1. fully understand the current project;
2. add FAISS;
3. improve retrieval quality;
4. improve evaluation;
5. polish the project as a portfolio artifact.

If unsure what to do next, the default next step is:

"Understand the baseline deeply, then implement the FAISS version."
