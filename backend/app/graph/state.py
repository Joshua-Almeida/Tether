from typing import Any, TypedDict


class CRAGState(TypedDict, total=False):
    question: str
    query: str
    rewrite_count: int
    documents: list[dict[str, Any]]
    graded: list[dict[str, Any]]
    answer: str
    citations: list[dict[str, Any]]
    decision: str
    refuse_reason: str
    error: str
    warnings: list[str]
