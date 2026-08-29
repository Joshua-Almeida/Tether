from __future__ import annotations

from typing import Any

from app.rag.store import retrieve_method
from app.schemas import AskResponse, Citation, GradedChunk, PipelineMode, PipelineTrace


def pipeline_steps(state: dict[str, Any], mode: PipelineMode) -> list[str]:
    if mode == "naive":
        return ["retrieve", "generate"]
    steps = ["retrieve", "grade"]
    if int(state.get("rewrite_count") or 0) > 0:
        steps.extend(["rewrite", "retrieve", "grade"])
    steps.append("generate" if state.get("decision") == "answer" else "refuse")
    return steps


def contrast_line(grounded: AskResponse, naive: AskResponse) -> str:
    if grounded.status == "refused" and naive.status == "answered":
        return (
            "Grounded refused. Naive answered anyway — that is uncited generation, "
            "the failure this desk exists to stop."
        )
    if grounded.status == "answered" and naive.status == "answered":
        return (
            "Both answered. Only the grounded folio is citation-gated; "
            "read the naive warnings before trusting it."
        )
    if grounded.status == "answered" and naive.status == "refused":
        return "Grounded answered from graded passages. Naive did not produce a usable folio."
    return "Both refused. The corpus could not support a cited answer."


def ask_response(state: dict[str, Any], mode: PipelineMode, latency_ms: int) -> AskResponse:
    decision = state.get("decision") or "refuse"
    citations = [Citation(**item) for item in state.get("citations") or []]
    graded = [GradedChunk(**item) for item in state.get("graded") or []]
    rewritten = state.get("query") if state.get("rewrite_count") else None
    warnings = list(state.get("warnings") or [])
    if mode == "naive" and "faithfulness_off" not in warnings:
        warnings.insert(0, "faithfulness_off")
    return AskResponse(
        status="answered" if decision == "answer" else "refused",
        answer=state.get("answer") or "",
        citations=citations,
        mode=mode,
        latency_ms=latency_ms,
        warnings=warnings,
        trace=PipelineTrace(
            rewritten_query=rewritten if isinstance(rewritten, str) else None,
            rewrite_count=int(state.get("rewrite_count") or 0),
            retrieved_count=len(state.get("documents") or []),
            graded=graded,
            decision="answer" if decision == "answer" else "refuse",
            refuse_reason=state.get("refuse_reason") or "",
            retrieval=retrieve_method(),
            steps=pipeline_steps(state, mode),
            mode=mode,
        ),
    )
