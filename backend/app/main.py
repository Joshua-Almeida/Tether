from __future__ import annotations

import json
import time
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.graph.crag import run_crag
from app.graph.naive import run_naive
from app.ingest import ingest, load_sources
from app.llm import LlmNotConfigured
from app.rag.store import chunk_count, listed_sources, retrieve_method
from app.respond import ask_response, contrast_line
from app.schemas import (
    AskRequest,
    AskResponse,
    CompareResponse,
    CorpusResponse,
    CorpusSource,
    HealthResponse,
    RetrievalEvalResponse,
    RetrievalEvalRow,
)

settings = get_settings()
app = FastAPI(title="Tether", version="0.2.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _require_ready() -> None:
    if not settings.llm_configured:
        raise HTTPException(
            status_code=503,
            detail="No LLM key found. Set FASTROUTER_API_KEY or OPENAI_API_KEY in .env.",
        )
    if chunk_count() == 0:
        raise HTTPException(
            status_code=409,
            detail="The index is empty. Use Ingest corpus on the desk first.",
        )


def _run_ask(question: str, mode: str) -> AskResponse:
    started = time.perf_counter()
    if mode == "naive":
        state = run_naive(question)
        payload = ask_response(state, "naive", int((time.perf_counter() - started) * 1000))
    else:
        state = run_crag(question)
        payload = ask_response(state, "grounded", int((time.perf_counter() - started) * 1000))
    return payload


@app.get("/api/health", response_model=HealthResponse)
def health() -> HealthResponse:
    count = chunk_count()
    return HealthResponse(
        ok=True,
        llm_configured=settings.llm_configured,
        index_ready=count > 0,
        chunk_count=count,
        sources=listed_sources(),
        retrieve_mode=retrieve_method(),
        rewrite_max=settings.rewrite_max,
    )


@app.get("/api/corpus", response_model=CorpusResponse)
def corpus() -> CorpusResponse:
    sources = [
        CorpusSource(id=str(item["id"]), title=str(item["title"]), url=str(item.get("url") or ""))
        for item in load_sources()
    ]
    return CorpusResponse(sources=sources)


@app.get("/api/eval/retrieval", response_model=RetrievalEvalResponse)
def eval_retrieval() -> RetrievalEvalResponse:
    if chunk_count() == 0:
        raise HTTPException(
            status_code=409,
            detail="The index is empty. Use Ingest corpus on the desk first.",
        )
    from evals.run_eval import retrieval_hit

    gold_path = Path(__file__).resolve().parents[1] / "evals" / "gold.json"
    gold = json.loads(gold_path.read_text(encoding="utf-8"))
    rows: list[RetrievalEvalRow] = []
    for row in gold["retrieval"]:
        hit = retrieval_hit(row["question"], row["must_sources"])
        rows.append(
            RetrievalEvalRow(
                id=row["id"],
                question=row["question"],
                must_sources=row["must_sources"],
                hit=hit,
            )
        )
    recall = sum(1 for row in rows if row.hit) / len(rows) if rows else 0.0
    return RetrievalEvalResponse(recall=recall, rows=rows)


@app.post("/api/ingest")
def ingest_corpus() -> dict:
    try:
        return ingest()
    except LlmNotConfigured as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Ingest failed: {exc}") from exc


@app.post("/api/ask", response_model=AskResponse)
def ask(payload: AskRequest) -> AskResponse:
    _require_ready()
    try:
        return _run_ask(payload.question, payload.mode)
    except LlmNotConfigured as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"RAG pipeline failed: {exc}") from exc


@app.post("/api/compare", response_model=CompareResponse)
def compare(payload: AskRequest) -> CompareResponse:
    _require_ready()
    try:
        grounded = _run_ask(payload.question, "grounded")
        naive = _run_ask(payload.question, "naive")
    except LlmNotConfigured as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"RAG pipeline failed: {exc}") from exc
    return CompareResponse(
        grounded=grounded,
        naive=naive,
        contrast=contrast_line(grounded, naive),
    )
