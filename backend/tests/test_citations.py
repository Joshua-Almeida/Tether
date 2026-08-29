from app.rag.citations import (
    filter_citations,
    is_refuse_text,
    parse_citation_ids,
    sentences_without_citations,
)


def test_parse_citation_ids_unique_order():
    ids = parse_citation_ids("IPv4 version is 4 bits [1]. The IHL is also 4 bits [1] [2].")
    assert ids == [1, 2]


def test_filter_citations_drops_uncited():
    citations = [
        {"id": 1, "source": "rfc791"},
        {"id": 2, "source": "rfc793"},
    ]
    kept = filter_citations("Only IPv4 facts here [1].", citations)
    assert kept == [{"id": 1, "source": "rfc791"}]


def test_refuse_text():
    assert is_refuse_text("REFUSE")
    assert is_refuse_text("refuse: not in corpus")
    assert not is_refuse_text("TCP uses a three-way handshake [1].")


def test_sentences_without_citations():
    missing = sentences_without_citations(
        "The version field is four bits [1]. This next claim has no source at all."
    )
    assert len(missing) == 1
    assert "no source" in missing[0]
