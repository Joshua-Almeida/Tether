# Architecture

Tether is a local cite-or-refuse RAG service. The UI is a Vite SPA. The API is FastAPI. The pipeline is a LangGraph StateGraph. Vectors sit in Chroma on disk. There is no Postgres, Daily, Studio, or other hosted database.

## Trees

```
frontend/
  index.html
  vite.config.ts          # host 127.0.0.1:5173, proxy /api → 127.0.0.1:8000
  src/
    main.tsx
    App.tsx               # desk (composer) + folio
    api.ts                # getHealth, ingestCorpus, askQuestion
    styles.css

backend/
  app/                    # Python package name is app — do not rename
    main.py               # FastAPI: /api/health, /api/ingest, /api/ask
    config.py             # pydantic-settings from repo-root .env
    llm.py                # ChatOpenAI + OpenAIEmbeddings
    ingest.py             # split RFC files, wipe + rebuild Chroma
    schemas.py
    graph/
      crag.py             # compile + run_crag
      nodes.py            # retrieve, grade, rewrite, generate, refuse
      state.py
    rag/
      store.py            # Chroma collection tether_rfc
      citations.py
  corpus/                 # RFC text + sources.json
  data/chroma/            # gitignored index
  evals/                  # gold.json + run_eval.py
  tests/
```

The git folder may still be named `grounded-rag`. That path is not the product name.

## Request flow

1. The desk POSTs JSON `{ "question": "..." }` to `/api/ask` (same origin via the Vite proxy).
2. `ask` in `app/main.py` rejects missing keys (**503**) and an empty index (**409**).
3. `run_crag(question)` invokes the compiled graph and returns `CRAGState`.
4. The handler maps `decision == "answer"` to `status: "answered"`, otherwise `refused`, plus `citations` and `trace`.

`GET /api/health` reports `llm_configured`, `index_ready`, `chunk_count`, and corpus source ids (from files, not from Chroma). `POST /api/ingest` rebuilds collection `tether_rfc` (deletes the collection, then adds chunks). It does not `rmtree` the persist folder, which locks on Windows while uvicorn is up.

Settings are loaded once (`lru_cache`). Restart uvicorn after editing `.env`.

## Graph

`build_crag_graph` in `app/graph/crag.py`:

- `START → retrieve → grade`
- `grade` → `route_after_grade` → `generate` | `rewrite` | `refuse`
- `rewrite → retrieve` (loop)
- `generate → END`, `refuse → END`

`route_after_grade` (`app/graph/nodes.py`):

- Any graded chunk with `relevant: true` → **generate**
- Else if `rewrite_count < REWRITE_MAX` (default **1**) → **rewrite**
- Else → **refuse**

Retrieve is dense-only: `Chroma.similarity_search` with `RETRIEVE_K` (default 6). There is no BM25 hybrid in this tree.

Grade asks the chat model for JSON `{ "grades": [{ "index", "relevant", "reason" }] }`. Relevance is a boolean from the LLM, not a cosine cutoff. There is no `GRADE_RELEVANCE_THRESHOLD` setting.

Generate keeps only passages marked relevant, numbers them `[1]…`, and requires citations. It refuses if the model returns `REFUSE`, if there are no `[n]` ids, or if `filter_citations` yields an empty list. `sentences_without_citations` exists and is unit-tested but is **not** called on the generate path yet.

`refuse_reason` is stored on graph state (`no_relevant_passages`, `generate_refused_or_uncited`, `citation_mismatch`, `graded_irrelevant`) but is **not** copied into `PipelineTrace` / the UI.

## Citations

`app/rag/citations.py`:

- `parse_citation_ids` — unique `[n]` in first-seen order
- `filter_citations` — keep numbered passages whose `id` appears in the answer
- `is_refuse_text` — empty or starts with `REFUSE`
- `sentences_without_citations` — sentences ≥ 24 chars with no `[n]` (unused in generate)

The API never returns footnotes for a refused answer.

## On-disk layout

| Path | Role |
|---|---|
| `backend/corpus/*.txt` | RFC excerpts (791, 793, 3986, 9110) |
| `backend/corpus/sources.json` | id, title, path, canonical URL |
| `backend/data/chroma/` | Chroma persist dir (`CHROMA_DIR`) |
| collection `tether_rfc` | Vector collection name |
| `backend/evals/gold.json` | Retrieval + refuse gold |
| `.env` | Secrets at **repo root** (also `backend/.env` if present) |

Chunking: `RecursiveCharacterTextSplitter`, `CHUNK_SIZE=800`, `CHUNK_OVERLAP=120`, separators `\n\n`, `\n`, `. `, ` `. Metadata: `source`, `title`, `url`, `chunk_id` as `{source_id}:{index}`.

## Env: FastRouter vs OpenAI

`app/config.py` prefers FastRouter when `FASTROUTER_API_KEY` is non-empty: chat `base_url` is `FASTROUTER_API_URL`, model is `FASTROUTER_LLM_MODEL`. Otherwise chat uses `OPENAI_API_KEY`, `OPENAI_BASE_URL`, `OPENAI_MODEL`.

Embeddings use `EMBEDDING_MODEL` (default `text-embedding-3-small`) on the **same gateway as chat**, unless `EMBEDDING_BASE_URL` / `EMBEDDING_API_KEY` are set. FastRouter serves this embedding id. A leftover `OPENAI_API_KEY` does not steal embedding traffic away from FastRouter (that used to 401 ingest when the OpenAI key was stale).

`llm_configured` is true when either chat key is set. Ingest and ask still need a working embedding endpoint.

CORS: `CORS_ORIGINS` for non-proxied browsers. The Vite app does not need CORS for `/api` because of the proxy.
