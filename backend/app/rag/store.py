from __future__ import annotations

from pathlib import Path

from chromadb import PersistentClient
from langchain_chroma import Chroma
from langchain_core.documents import Document

from app.config import BACKEND_DIR, get_settings
from app.llm import embedding_model

COLLECTION = "tether_rfc"


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
    settings = get_settings()
    settings.chroma_path.mkdir(parents=True, exist_ok=True)
    client = PersistentClient(path=str(settings.chroma_path))
    try:
        client.delete_collection(COLLECTION)
    except Exception:
        pass


def retrieve(question: str, k: int | None = None) -> list[Document]:
    settings = get_settings()
    store = chroma()
    return store.similarity_search(question, k=k or settings.retrieve_k)


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


def listed_sources() -> list[str]:
    return sorted(
        path.stem for path in corpus_dir().glob("*.txt") if path.name.lower() != "license.txt"
    )
