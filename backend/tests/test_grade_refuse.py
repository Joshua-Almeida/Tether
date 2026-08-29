from app.graph.nodes import REFUSE_ANSWER, generate_node, route_after_grade


def test_route_generate_when_relevant():
    state = {
        "graded": [{"chunk_id": "a", "relevant": True}],
        "rewrite_count": 0,
    }
    assert route_after_grade(state) == "generate"


def test_route_rewrite_when_all_irrelevant():
    state = {
        "graded": [{"chunk_id": "a", "relevant": False}],
        "rewrite_count": 0,
    }
    assert route_after_grade(state) == "rewrite"


def test_route_refuse_after_rewrite_budget():
    state = {
        "graded": [{"chunk_id": "a", "relevant": False}],
        "rewrite_count": 1,
    }
    assert route_after_grade(state) == "refuse"


def test_generate_refuses_without_relevant_passages():
    result = generate_node(
        {
            "question": "Who won the World Cup?",
            "documents": [{"chunk_id": "a", "content": "IPv4", "source": "rfc791", "title": "", "url": ""}],
            "graded": [{"chunk_id": "a", "relevant": False}],
        }
    )
    assert result["decision"] == "refuse"
    assert result["citations"] == []
    assert result["answer"] == REFUSE_ANSWER
