from __future__ import annotations

import json
import re
from typing import Any

from langchain_core.documents import Document
from langchain_core.messages import HumanMessage, SystemMessage

from app.config import get_settings
from app.graph.state import CRAGState
from app.llm import chat_model
from app.rag.citations import (
    filter_citations,
    is_refuse_text,
    parse_citation_ids,
    sentences_without_citations,
)
from app.rag.store import retrieve

REFUSE_ANSWER = (
    "I cannot answer from the local corpus. Retrieved passages were not relevant "
    "enough to cite, including after a query rewrite."
)

GRADE_SYSTEM = (
    "You are a strict relevance grader for corrective RAG. "
    "A passage is relevant only if it contains facts that could support answering the question. "
    "Score each passage from 0 to 1. Return JSON only."
)

REWRITE_SYSTEM = (
    "Rewrite the user question to improve retrieval over a corpus of IETF RFC excerpts "
    "(IPv4, TCP, URI syntax, HTTP semantics). Keep a single concise question. "
    "Do not answer it."
)

GENERATE_SYSTEM = (
    "You answer questions using ONLY the numbered passages. "
    "Every factual sentence must include a citation like [1] or [2] matching a passage. "
    "If the passages do not contain the answer, reply with exactly REFUSE. "
    "Do not use outside knowledge. Do not invent citations."
)

JSON_BLOCK = re.compile(r"\{.*\}", re.DOTALL)


def document_to_dict(doc: Document) -> dict[str, Any]:
    return {
        "content": doc.page_content,
        "source": str(doc.metadata.get("source", "unknown")),
        "title": str(doc.metadata.get("title", "")),
        "url": str(doc.metadata.get("url", "")),
        "chunk_id": str(doc.metadata.get("chunk_id", "")),
        "section": str(doc.metadata.get("section", "")),
    }


def route_after_grade(state: CRAGState) -> str:
    relevant = [item for item in state.get("graded", []) if item.get("relevant")]
    if relevant:
        return "generate"
    settings = get_settings()
    if int(state.get("rewrite_count", 0)) < settings.rewrite_max:
        return "rewrite"
    return "refuse"


def retrieve_node(state: CRAGState) -> dict[str, Any]:
    query = state.get("query") or state["question"]
    docs = retrieve(query)
    return {
        "query": query,
        "documents": [document_to_dict(doc) for doc in docs],
    }


def _score_relevant(row: dict[str, Any], threshold: float) -> bool:
    raw = row.get("score")
    if raw is not None and raw != "":
        try:
            return float(raw) >= threshold
        except (TypeError, ValueError):
            pass
    return bool(row.get("relevant", False))


def _parse_grades(
    raw: str,
    documents: list[dict[str, Any]],
    threshold: float | None = None,
) -> list[dict[str, Any]]:
    cutoff = get_settings().grade_relevance_threshold if threshold is None else threshold
    match = JSON_BLOCK.search(raw or "")
    payload = json.loads(match.group(0) if match else raw)
    by_index: dict[int, dict[str, Any]] = {}
    for row in payload.get("grades", []):
        by_index[int(row["index"])] = row
    graded: list[dict[str, Any]] = []
    for index, doc in enumerate(documents, start=1):
        row = by_index.get(index, {})
        raw_score = row.get("score")
        score: float | None
        try:
            score = float(raw_score) if raw_score is not None and raw_score != "" else None
        except (TypeError, ValueError):
            score = None
        snippet = " ".join(str(doc.get("content") or "").split())
        graded.append(
            {
                "chunk_id": doc["chunk_id"],
                "source": doc["source"],
                "relevant": _score_relevant(row, cutoff),
                "reason": str(row.get("reason", "no grade returned")),
                "score": score,
                "snippet": snippet[:220],
                "section": str(doc.get("section") or ""),
            }
        )
    return graded


def grade_node(state: CRAGState) -> dict[str, Any]:
    documents = state.get("documents") or []
    if not documents:
        return {"graded": []}
    lines = []
    for index, doc in enumerate(documents, start=1):
        lines.append(f"[{index}] source={doc['source']} id={doc['chunk_id']}\n{doc['content']}")
    prompt = (
        f"Question: {state['question']}\n\nPassages:\n"
        + "\n\n".join(lines)
        + '\n\nReturn JSON: {"grades":[{"index":1,"score":0.8,"reason":"short"}]}'
    )
    message = chat_model().invoke(
        [SystemMessage(content=GRADE_SYSTEM), HumanMessage(content=prompt)]
    )
    return {"graded": _parse_grades(str(message.content), documents)}


def rewrite_node(state: CRAGState) -> dict[str, Any]:
    prompt = f"Original question: {state['question']}"
    message = chat_model().invoke(
        [SystemMessage(content=REWRITE_SYSTEM), HumanMessage(content=prompt)]
    )
    rewritten = str(message.content).strip().splitlines()[0].strip().strip('"')
    return {
        "query": rewritten or state["question"],
        "rewrite_count": int(state.get("rewrite_count", 0)) + 1,
        "documents": [],
        "graded": [],
    }


def _refuse(reason: str) -> dict[str, Any]:
    return {
        "decision": "refuse",
        "answer": REFUSE_ANSWER,
        "citations": [],
        "refuse_reason": reason,
    }


def finalize_generate(answer: str, numbered: list[dict[str, Any]]) -> dict[str, Any]:
    if is_refuse_text(answer) or not parse_citation_ids(answer):
        return _refuse("generate_refused_or_uncited")
    citations = filter_citations(answer, numbered)
    if not citations:
        return _refuse("citation_mismatch")
    if sentences_without_citations(answer):
        return _refuse("uncited_sentences")
    return {
        "decision": "answer",
        "answer": answer,
        "citations": citations,
        "refuse_reason": "",
    }


def generate_node(state: CRAGState) -> dict[str, Any]:
    relevant_ids = {item["chunk_id"] for item in state.get("graded", []) if item.get("relevant")}
    passages = [doc for doc in state.get("documents", []) if doc["chunk_id"] in relevant_ids]
    if not passages:
        return _refuse("no_relevant_passages")
    numbered: list[dict[str, Any]] = []
    lines: list[str] = []
    for index, doc in enumerate(passages, start=1):
        numbered.append(
            {
                "id": index,
                "source": doc["source"],
                "title": doc["title"],
                "url": doc["url"],
                "chunk_id": doc["chunk_id"],
                "quote": doc["content"][:500],
                "section": str(doc.get("section") or ""),
            }
        )
        lines.append(f"[{index}] ({doc['source']}) {doc['content']}")
    prompt = f"Question: {state['question']}\n\nPassages:\n" + "\n\n".join(lines)
    message = chat_model(temperature=0).invoke(
        [SystemMessage(content=GENERATE_SYSTEM), HumanMessage(content=prompt)]
    )
    return finalize_generate(str(message.content).strip(), numbered)


def refuse_node(state: CRAGState) -> dict[str, Any]:
    return _refuse(state.get("refuse_reason") or "graded_irrelevant")
