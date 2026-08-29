from __future__ import annotations

from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from app.graph.nodes import document_to_dict
from app.graph.state import CRAGState
from app.llm import chat_model
from app.rag.citations import (
    filter_citations,
    parse_citation_ids,
    sentences_without_citations,
)
from app.rag.store import retrieve

NAIVE_SYSTEM = (
    "Answer the user question helpfully. Use the passages if they seem useful. "
    "You may also use general knowledge when the passages do not contain the answer. "
    "Citations like [1] are optional. Do not reply with REFUSE."
)


def _number_passages(passages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    numbered: list[dict[str, Any]] = []
    for index, doc in enumerate(passages, start=1):
        numbered.append(
            {
                "id": index,
                "source": doc.get("source", ""),
                "title": doc.get("title", ""),
                "url": doc.get("url", ""),
                "chunk_id": doc.get("chunk_id", ""),
                "quote": str(doc.get("content") or "")[:500],
                "section": str(doc.get("section") or ""),
            }
        )
    return numbered


def naive_warnings(answer: str, numbered: list[dict[str, Any]]) -> list[str]:
    warnings = ["faithfulness_off"]
    if sentences_without_citations(answer):
        warnings.append("uncited_sentences")
    cited = parse_citation_ids(answer)
    valid = {item["id"] for item in numbered}
    if cited and any(item not in valid for item in cited):
        warnings.append("invented_citations")
    if cited and not filter_citations(answer, numbered):
        warnings.append("citation_mismatch")
    if not cited:
        warnings.append("no_citations")
    return warnings


def run_naive(question: str) -> CRAGState:
    text = question.strip()
    docs = retrieve(text)
    documents = [document_to_dict(doc) for doc in docs]
    numbered = _number_passages(documents)
    lines = [
        f"[{item['id']}] ({item['source']}) {item['quote']}"
        for item in numbered
    ]
    prompt = f"Question: {text}\n\nPassages:\n" + ("\n\n".join(lines) or "(none)")
    message = chat_model(temperature=0).invoke(
        [SystemMessage(content=NAIVE_SYSTEM), HumanMessage(content=prompt)]
    )
    answer = str(message.content).strip()
    citations = filter_citations(answer, numbered)
    return {
        "question": text,
        "query": text,
        "rewrite_count": 0,
        "documents": documents,
        "graded": [],
        "answer": answer,
        "citations": citations,
        "decision": "answer",
        "refuse_reason": "",
        "error": "",
        "warnings": naive_warnings(answer, numbered),
    }
