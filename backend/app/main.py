from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.graph.crag import run_crag
from app.ingest import ingest
from app.llm import LlmNotConfigured
from app.rag.store import chunk_count, listed_sources
from app.schemas import AskRequest, AskResponse, Citation, GradedChunk, HealthResponse, PipelineTrace

settings = get_settings()
app = FastAPI(title="Tether", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health", response_model=HealthResponse)
def health() -> HealthResponse:
    count = chunk_count()
    return HealthResponse(
        ok=True,
        llm_configured=settings.llm_configured,
        index_ready=count > 0,
        chunk_count=count,
        sources=listed_sources(),
    )


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
    try:
        state = run_crag(payload.question)
    except LlmNotConfigured as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"RAG pipeline failed: {exc}") from exc

    decision = state.get("decision") or "refuse"
    citations = [Citation(**item) for item in state.get("citations") or []]
    graded = [GradedChunk(**item) for item in state.get("graded") or []]
    return AskResponse(
        status="answered" if decision == "answer" else "refused",
        answer=state.get("answer") or "",
        citations=citations,
        trace=PipelineTrace(
            rewritten_query=state.get("query") if state.get("rewrite_count") else None,
            rewrite_count=int(state.get("rewrite_count") or 0),
            retrieved_count=len(state.get("documents") or []),
            graded=graded,
            decision="answer" if decision == "answer" else "refuse",
            refuse_reason=state.get("refuse_reason") or "",
        ),
    )
