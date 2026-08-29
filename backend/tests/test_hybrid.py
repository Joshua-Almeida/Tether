from langchain_core.documents import Document

from app.rag.hybrid import BM25Index, rrf_fuse, tokenize


def test_tokenize_lowercases_and_keeps_digits():
    assert tokenize("IHL is 4 bits.") == ["ihl", "is", "4", "bits"]


def test_rrf_ranks_shared_ids_first():
    fused = rrf_fuse(["a", "b", "c"], ["a", "c", "b"])
    assert fused[0] == "a"
    assert set(fused) == {"a", "b", "c"}


def test_bm25_prefers_exact_protocol_tokens():
    docs = [
        Document(page_content="The IHL field is four bits.", metadata={"chunk_id": "ihl"}),
        Document(page_content="Football is played on grass.", metadata={"chunk_id": "sport"}),
    ]
    ranked = BM25Index(docs).rank("IHL bits", k=2)
    assert ranked[0].metadata["chunk_id"] == "ihl"
