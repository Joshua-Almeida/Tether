from app.ingest import split_corpus
from app.rag.citations import parse_citation_ids


def test_corpus_splits_with_source_metadata():
    docs = split_corpus()
    sources = {doc.metadata["source"] for doc in docs}
    assert sources == {"rfc791", "rfc793", "rfc3986", "rfc9110"}
    assert all(doc.metadata["chunk_id"] for doc in docs)
    assert all(doc.page_content.strip() for doc in docs)


def test_citation_format_is_bracketed_integers():
    answer = "HTTP default port is 80 [3]. HTTPS default port is 443 [3]."
    assert parse_citation_ids(answer) == [3]
