# Tether

Cite-or-refuse RAG. Upload a paper (or load the bundled IETF RFC excerpts), ask a question, and the desk either answers with numbered footnotes or refuses. It does not invent sources from model memory.

**Grounded** is Corrective RAG: hybrid retrieve (dense + BM25), grade, optional rewrite, then a faithfulness gate. **Naive** is ordinary retrieve-then-generate. **Compare** runs both on the same question.

## Features

- Upload PDF, `.txt`, or Markdown and ask against *your* files
- Cite-or-refuse answers with clickable footnotes
- Grounded vs naive compare
- Inspectable pipeline trace (retrieve, grade, rewrite, decision)
- Local Chroma index — no hosted database
- Retrieval gold eval over the RFC demo

## Stack

FastAPI, LangGraph, Chroma, React + Vite. Chat and embeddings go through FastRouter or any OpenAI-compatible API.

## Setup

```bash
cp .env.example .env
```

Set `FASTROUTER_API_KEY` or `OPENAI_API_KEY`. Do not commit `.env`.

**API** (from the repo root, Python 3.11+):

```bash
python -m venv backend/.venv
# Windows: backend\.venv\Scripts\Activate.ps1
# macOS / Linux: source backend/.venv/bin/activate
pip install -r backend/requirements.txt
```

```powershell
# From grounded-rag, frontend, or backend — two terminals:
.\scripts\dev-api.ps1
.\scripts\dev-web.ps1
```

Open [http://127.0.0.1:5173](http://127.0.0.1:5173). The API is [http://127.0.0.1:8765](http://127.0.0.1:8765) (not 8000).

## Use

1. Drop a PDF or text file on the **Shelf**, or click **Load RFC demo**.
2. Ask in **Grounded** mode. Off-corpus questions should refuse.
3. Use **Compare** on something the documents cannot answer (e.g. “Who won the 2018 FIFA World Cup?”).

Ask returns 409 until at least one document is indexed.

## Tests

```bash
cd backend
# Windows: $env:PYTHONPATH = "."
export PYTHONPATH=.
pytest
python evals/run_eval.py --skip-llm
```

`--skip-llm` scores retrieval gold only (needs an index and embeddings). Full `python evals/run_eval.py` calls the live graph.

## Docs

- [Architecture](docs/ARCHITECTURE.md)
- [Design](docs/DESIGN.md)
- [Study notes](docs/STUDY.md)
