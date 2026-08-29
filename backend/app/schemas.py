from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

PipelineMode = Literal["grounded", "naive"]
RetrieveMethod = Literal["hybrid", "dense"]


class AskRequest(BaseModel):
    question: str = Field(min_length=3, max_length=2000)
    mode: PipelineMode = "grounded"


class Citation(BaseModel):
    id: int
    source: str
    title: str
    url: str = ""
    chunk_id: str
    quote: str
    section: str = ""


class GradedChunk(BaseModel):
    chunk_id: str
    source: str
    relevant: bool
    reason: str
    score: float | None = None
    snippet: str = ""
    section: str = ""


class PipelineTrace(BaseModel):
    rewritten_query: str | None = None
    rewrite_count: int = 0
    retrieved_count: int = 0
    graded: list[GradedChunk] = Field(default_factory=list)
    decision: Literal["answer", "refuse"] = "refuse"
    refuse_reason: str = ""
    retrieval: RetrieveMethod = "hybrid"
    steps: list[str] = Field(default_factory=list)
    mode: PipelineMode = "grounded"


class AskResponse(BaseModel):
    status: Literal["answered", "refused"]
    answer: str
    citations: list[Citation] = Field(default_factory=list)
    trace: PipelineTrace
    error: str | None = None
    mode: PipelineMode = "grounded"
    latency_ms: int = 0
    warnings: list[str] = Field(default_factory=list)


class CompareResponse(BaseModel):
    grounded: AskResponse
    naive: AskResponse
    contrast: str


class HealthResponse(BaseModel):
    ok: bool
    llm_configured: bool
    index_ready: bool
    chunk_count: int
    sources: list[str] = Field(default_factory=list)
    retrieve_mode: RetrieveMethod = "hybrid"
    rewrite_max: int = 1


class CorpusSource(BaseModel):
    id: str
    title: str
    url: str


class CorpusResponse(BaseModel):
    sources: list[CorpusSource] = Field(default_factory=list)


class LibrarySource(BaseModel):
    id: str
    title: str
    filename: str = ""
    origin: str = "upload"
    chunks: int = 0
    url: str = ""


class LibraryResponse(BaseModel):
    sources: list[LibrarySource] = Field(default_factory=list)


class RetrievalEvalRow(BaseModel):
    id: str
    question: str
    must_sources: list[str]
    hit: bool


class RetrievalEvalResponse(BaseModel):
    recall: float
    rows: list[RetrievalEvalRow] = Field(default_factory=list)
