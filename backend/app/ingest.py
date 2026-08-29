from __future__ import annotations

import json

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.config import get_settings
from app.llm import require_llm
from app.rag.store import chroma, corpus_dir, reset_collection


def load_sources() -> list[dict]:
    path = corpus_dir() / "sources.json"
    return json.loads(path.read_text(encoding="utf-8"))


def split_corpus() -> list[Document]:
    settings = get_settings()
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        separators=["\n\n", "\n", ". ", " "],
    )
    documents: list[Document] = []
    for source in load_sources():
        text_path = corpus_dir() / source["path"]
        text = text_path.read_text(encoding="utf-8")
        chunks = splitter.split_text(text)
        for index, chunk in enumerate(chunks):
            chunk_id = f"{source['id']}:{index}"
            documents.append(
                Document(
                    page_content=chunk,
                    metadata={
                        "source": source["id"],
                        "title": source["title"],
                        "url": source["url"],
                        "chunk_id": chunk_id,
                    },
                )
            )
    return documents


def ingest() -> dict:
    require_llm()
    settings = get_settings()
    persist = settings.chroma_path
    persist.mkdir(parents=True, exist_ok=True)
    reset_collection()
    documents = split_corpus()
    store = chroma()
    store.add_documents(documents)
    return {
        "chunks": len(documents),
        "sources": sorted({str(doc.metadata["source"]) for doc in documents}),
        "persist": str(persist),
    }


def main() -> None:
    result = ingest()
    print(f"Ingested {result['chunks']} chunks from {', '.join(result['sources'])}")
    print(f"Index: {result['persist']}")


if __name__ == "__main__":
    main()
