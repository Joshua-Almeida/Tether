from app.graph.nodes import (
    REFUSE_ANSWER,
    _parse_grades,
    finalize_generate,
    generate_node,
    route_after_grade,
)


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
    assert result["refuse_reason"] == "no_relevant_passages"


def test_finalize_refuses_uncited_sentences():
    numbered = [{"id": 1, "source": "rfc791", "title": "IP", "url": "", "chunk_id": "a", "quote": "version"}]
    result = finalize_generate(
        "The version field is four bits [1]. This next claim has no source at all.",
        numbered,
    )
    assert result["decision"] == "refuse"
    assert result["citations"] == []
    assert result["refuse_reason"] == "uncited_sentences"


def test_finalize_answers_when_every_long_sentence_is_cited():
    numbered = [{"id": 1, "source": "rfc791", "title": "IP", "url": "", "chunk_id": "a", "quote": "version"}]
    result = finalize_generate("The IPv4 version field is four bits long [1].", numbered)
    assert result["decision"] == "answer"
    assert result["citations"] == numbered


def test_grade_score_below_threshold_is_irrelevant():
    docs = [{"chunk_id": "a", "source": "rfc791"}]
    graded = _parse_grades(
        '{"grades":[{"index":1,"score":0.2,"reason":"weak"}]}',
        docs,
        threshold=0.5,
    )
    assert graded[0]["relevant"] is False


def test_grade_score_at_threshold_is_relevant():
    docs = [{"chunk_id": "a", "source": "rfc791"}]
    graded = _parse_grades(
        '{"grades":[{"index":1,"score":0.5,"reason":"enough"}]}',
        docs,
        threshold=0.5,
    )
    assert graded[0]["relevant"] is True
