from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class AskRequest(BaseModel):
    question: str = Field(min_length=3, max_length=2000)


class Citation(BaseModel):
    id: int
    source: str
    title: str
    url: str = ""
    chunk_id: str
    quote: str


class GradedChunk(BaseModel):
    chunk_id: str
    source: str
    relevant: bool
    reason: str


class PipelineTrace(BaseModel):
    rewritten_query: str | None = None
    rewrite_count: int = 0
    retrieved_count: int = 0
    graded: list[GradedChunk] = Field(default_factory=list)
    decision: Literal["answer", "refuse"] = "refuse"


class AskResponse(BaseModel):
    status: Literal["answered", "refused"]
    answer: str
    citations: list[Citation] = Field(default_factory=list)
    trace: PipelineTrace
    error: str | None = None


class HealthResponse(BaseModel):
    ok: bool
    llm_configured: bool
    index_ready: bool
    chunk_count: int
    sources: list[str] = Field(default_factory=list)
