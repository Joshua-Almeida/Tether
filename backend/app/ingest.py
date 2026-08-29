from __future__ import annotations

import json
import re

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.config import get_settings
from app.llm import require_llm
from app.rag.store import chroma, clear_lexical_index, corpus_dir, reset_collection

SECTION_RE = re.compile(r"^(\d+(?:\.\d+)*)\.?\s+(\S.*)$")


def load_sources() -> list[dict]:
    path = corpus_dir() / "sources.json"
    return json.loads(path.read_text(encoding="utf-8"))


def heading_for_chunk(text: str, chunk: str) -> str:
    needle = (chunk or "").strip()[:80]
    pos = text.find(needle) if needle else -1
    prefix = text[: pos if pos >= 0 else 0]
    heading = ""
    for line in prefix.splitlines():
        match = SECTION_RE.match(line.strip())
        if match:
            heading = f"{match.group(1)} {match.group(2).strip()}"
    return heading[:160]


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
                        "section": heading_for_chunk(text, chunk),
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
    clear_lexical_index()
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
