from app.graph.naive import naive_warnings
from app.respond import ask_response, contrast_line, pipeline_steps


def test_naive_warnings_flag_memory_answers():
    numbered = [{"id": 1, "source": "rfc791"}]
    warnings = naive_warnings("France won the 2018 FIFA World Cup.", numbered)
    assert "faithfulness_off" in warnings
    assert "no_citations" in warnings
    assert "uncited_sentences" in warnings


def test_naive_warnings_catch_invented_ids():
    numbered = [{"id": 1, "source": "rfc791"}]
    warnings = naive_warnings("TTL is eight bits [9].", numbered)
    assert "invented_citations" in warnings


def test_pipeline_steps_include_rewrite_loop():
    assert pipeline_steps({"rewrite_count": 0, "decision": "answer"}, "grounded") == [
        "retrieve",
        "grade",
        "generate",
    ]
    assert pipeline_steps({"rewrite_count": 1, "decision": "refuse"}, "grounded") == [
        "retrieve",
        "grade",
        "rewrite",
        "retrieve",
        "grade",
        "refuse",
    ]
    assert pipeline_steps({}, "naive") == ["retrieve", "generate"]


def test_contrast_calls_out_hallucination_gap():
    grounded = ask_response(
        {"decision": "refuse", "answer": "no", "citations": [], "graded": [], "documents": []},
        "grounded",
        10,
    )
    naive = ask_response(
        {
            "decision": "answer",
            "answer": "France.",
            "citations": [],
            "graded": [],
            "documents": [],
            "warnings": ["faithfulness_off", "no_citations"],
        },
        "naive",
        12,
    )
    line = contrast_line(grounded, naive)
    assert "refused" in line.lower()
    assert "naive" in line.lower()


def test_ask_response_exposes_latency_and_mode():
    payload = ask_response(
        {
            "decision": "answer",
            "answer": "The version field is four bits [1].",
            "citations": [
                {
                    "id": 1,
                    "source": "rfc791",
                    "title": "IP",
                    "url": "",
                    "chunk_id": "rfc791:0",
                    "quote": "Version: 4 bits",
                }
            ],
            "graded": [
                {
                    "chunk_id": "rfc791:0",
                    "source": "rfc791",
                    "relevant": True,
                    "reason": "states field width",
                    "score": 0.9,
                    "snippet": "Version: 4 bits",
                }
            ],
            "documents": [{}],
            "rewrite_count": 0,
        },
        "grounded",
        842,
    )
    assert payload.mode == "grounded"
    assert payload.latency_ms == 842
    assert payload.trace.steps[-1] == "generate"
    assert payload.trace.graded[0].score == 0.9
