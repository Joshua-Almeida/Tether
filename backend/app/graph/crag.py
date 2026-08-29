from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from app.graph.nodes import (
    generate_node,
    grade_node,
    refuse_node,
    retrieve_node,
    rewrite_node,
    route_after_grade,
)
from app.graph.state import CRAGState


def build_crag_graph():
    graph = StateGraph(CRAGState)
    graph.add_node("retrieve", retrieve_node)
    graph.add_node("grade", grade_node)
    graph.add_node("rewrite", rewrite_node)
    graph.add_node("generate", generate_node)
    graph.add_node("refuse", refuse_node)

    graph.add_edge(START, "retrieve")
    graph.add_edge("retrieve", "grade")
    graph.add_conditional_edges(
        "grade",
        route_after_grade,
        {"generate": "generate", "rewrite": "rewrite", "refuse": "refuse"},
    )
    graph.add_edge("rewrite", "retrieve")
    graph.add_edge("generate", END)
    graph.add_edge("refuse", END)
    return graph.compile()


CRAG = None


def crag_app():
    global CRAG
    if CRAG is None:
        CRAG = build_crag_graph()
    return CRAG


def run_crag(question: str) -> CRAGState:
    initial: CRAGState = {
        "question": question.strip(),
        "query": question.strip(),
        "rewrite_count": 0,
        "documents": [],
        "graded": [],
        "answer": "",
        "citations": [],
        "decision": "refuse",
        "refuse_reason": "",
        "error": "",
    }
    return crag_app().invoke(initial)
