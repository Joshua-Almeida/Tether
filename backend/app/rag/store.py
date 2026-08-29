from __future__ import annotations

import threading
from pathlib import Path

from chromadb import PersistentClient
from langchain_chroma import Chroma
from langchain_core.documents import Document

from app.config import BACKEND_DIR, get_settings
from app.llm import embedding_model
from app.rag.hybrid import BM25Index, rrf_fuse

COLLECTION = "tether_rfc"

_INDEX_LOCK = threading.Lock()
_lexical: BM25Index | None = None
_lexical_n = -1


def chroma() -> Chroma:
    settings = get_settings()
    settings.chroma_path.mkdir(parents=True, exist_ok=True)
    return Chroma(
        collection_name=COLLECTION,
        persist_directory=str(settings.chroma_path),
        embedding_function=embedding_model(settings),
    )


def corpus_dir() -> Path:
    return BACKEND_DIR / "corpus"


def reset_collection() -> None:
    with _INDEX_LOCK:
        settings = get_settings()
        settings.chroma_path.mkdir(parents=True, exist_ok=True)
        client = PersistentClient(path=str(settings.chroma_path))
        try:
            client.delete_collection(COLLECTION)
        except Exception:
            pass
        clear_lexical_index()


def add_documents(documents: list[Document]) -> None:
    with _INDEX_LOCK:
        chroma().add_documents(documents)
        clear_lexical_index()


def clear_lexical_index() -> None:
    global _lexical, _lexical_n
    _lexical = None
    _lexical_n = -1


def load_indexed_documents() -> list[Document]:
    settings = get_settings()
    if not settings.chroma_path.exists():
        return []
    try:
        client = PersistentClient(path=str(settings.chroma_path))
        collection = client.get_or_create_collection(COLLECTION)
        data = collection.get(include=["documents", "metadatas"])
    except Exception:
        return []
    documents: list[Document] = []
    for content, meta in zip(data.get("documents") or [], data.get("metadatas") or []):
        if not content:
            continue
        documents.append(Document(page_content=content, metadata=meta or {}))
    return documents


def lexical_index() -> BM25Index:
    global _lexical, _lexical_n
    count = chunk_count()
    if _lexical is None or _lexical_n != count:
        _lexical = BM25Index(load_indexed_documents())
        _lexical_n = count
    return _lexical


def _chunk_id(doc: Document) -> str:
    return str(doc.metadata.get("chunk_id") or "")


def retrieve(question: str, k: int | None = None, mode: str | None = None) -> list[Document]:
    settings = get_settings()
    top_k = k or settings.retrieve_k
    method = (mode or settings.retrieve_mode or "hybrid").strip().lower()
    dense = chroma().similarity_search(question, k=top_k)
    if method == "dense":
        return dense
    try:
        sparse = lexical_index().rank(question, k=top_k)
    except Exception:
        return dense
    if not sparse:
        return dense
    by_id: dict[str, Document] = {}
    for doc in dense + sparse:
        key = _chunk_id(doc)
        if key:
            by_id[key] = doc
    fused = rrf_fuse(
        [_chunk_id(doc) for doc in dense],
        [_chunk_id(doc) for doc in sparse],
    )
    out: list[Document] = []
    for key in fused:
        doc = by_id.get(key)
        if doc is None:
            continue
        out.append(doc)
        if len(out) >= top_k:
            break
    return out or dense


def chunk_count() -> int:
    settings = get_settings()
    if not settings.chroma_path.exists():
        return 0
    try:
        client = PersistentClient(path=str(settings.chroma_path))
        collection = client.get_or_create_collection(COLLECTION)
        return int(collection.count())
    except Exception:
        return 0


def sources_from_index() -> list[str]:
    found: set[str] = set()
    for doc in load_indexed_documents():
        source = str(doc.metadata.get("source") or "").strip()
        if source:
            found.add(source)
    return sorted(found)


def delete_by_source(source_id: str) -> None:
    with _INDEX_LOCK:
        settings = get_settings()
        if not settings.chroma_path.exists():
            return
        try:
            client = PersistentClient(path=str(settings.chroma_path))
            collection = client.get_or_create_collection(COLLECTION)
            collection.delete(where={"source": source_id})
        except Exception:
            pass
        clear_lexical_index()


def listed_sources() -> list[str]:
    indexed = sources_from_index()
    if indexed:
        return indexed
    return sorted(
        path.stem for path in corpus_dir().glob("*.txt") if path.name.lower() != "license.txt"
    )


def retrieve_method() -> str:
    method = (get_settings().retrieve_mode or "hybrid").strip().lower()
    return "dense" if method == "dense" else "hybrid"
