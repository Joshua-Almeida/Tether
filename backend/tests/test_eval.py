from evals.run_eval import citation_precision, faith_ok, retrieval_hit


class _Doc:
    def __init__(self, source: str):
        self.metadata = {"source": source}


def test_retrieval_hit_needs_every_source(monkeypatch):
    monkeypatch.setattr(
        "evals.run_eval.retrieve",
        lambda question, k=6: [_Doc("rfc791"), _Doc("rfc793")],
    )
    assert retrieval_hit("q", ["rfc791"]) is True
    assert retrieval_hit("q", ["rfc791", "rfc9110"]) is False


def test_citation_precision_ignores_unknown_ids():
    assert citation_precision("Ports are 80 [1] and 443 [9].", [{"id": 1}]) == 0.5


def test_faith_ok_rejects_uncited_sentence():
    state = {
        "decision": "answer",
        "answer": "The version field is four bits [1]. This next claim has no source at all.",
        "citations": [{"id": 1}],
    }
    assert faith_ok(state) is False


def test_faith_ok_accepts_fully_cited_answer():
    state = {
        "decision": "answer",
        "answer": "The IPv4 version field is four bits long [1].",
        "citations": [{"id": 1}],
    }
    assert faith_ok(state) is True
