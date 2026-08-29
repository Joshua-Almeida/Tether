from __future__ import annotations

import json
import re

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.config import get_settings
from app.library import upsert_catalog
from app.llm import require_llm
from app.rag.extract import extract_text, source_id_for, title_for
from app.rag.store import add_documents, corpus_dir, delete_by_source

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


def split_text(
    text: str,
    source_id: str,
    title: str,
    url: str = "",
    origin: str = "demo",
) -> list[Document]:
    settings = get_settings()
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        separators=["\n\n", "\n", ". ", " "],
    )
    documents: list[Document] = []
    for index, chunk in enumerate(splitter.split_text(text)):
        documents.append(
            Document(
                page_content=chunk,
                metadata={
                    "source": source_id,
                    "title": title,
                    "url": url,
                    "chunk_id": f"{source_id}:{index}",
                    "section": heading_for_chunk(text, chunk),
                    "origin": origin,
                },
            )
        )
    return documents


def split_corpus() -> list[Document]:
    documents: list[Document] = []
    for source in load_sources():
        text = (corpus_dir() / source["path"]).read_text(encoding="utf-8")
        documents.extend(
            split_text(
                text,
                source_id=str(source["id"]),
                title=str(source["title"]),
                url=str(source.get("url") or ""),
                origin="demo",
            )
        )
    return documents


def _index_documents(documents: list[Document], entries: list[dict]) -> dict:
    ids = {str(doc.metadata["source"]) for doc in documents}
    for source_id in ids:
        delete_by_source(source_id)
    add_documents(documents)
    upsert_catalog(entries)
    return {
        "chunks": len(documents),
        "sources": sorted(ids),
        "persist": str(get_settings().chroma_path),
    }


def ingest() -> dict:
    require_llm()
    documents = split_corpus()
    counts: dict[str, int] = {}
    for doc in documents:
        source_id = str(doc.metadata["source"])
        counts[source_id] = counts.get(source_id, 0) + 1
    titles = {str(item["id"]): str(item["title"]) for item in load_sources()}
    entries = [
        {
            "id": source_id,
            "title": titles.get(source_id, source_id),
            "filename": "",
            "origin": "demo",
            "chunks": counts[source_id],
        }
        for source_id in counts
    ]
    return _index_documents(documents, entries)


def ingest_uploads(files: list[tuple[str, bytes]]) -> dict:
    require_llm()
    documents: list[Document] = []
    entries: list[dict] = []
    for filename, data in files:
        text = extract_text(filename, data)
        if not text.strip():
            raise ValueError(f"{filename} has no extractable text.")
        source_id = source_id_for(filename)
        title = title_for(filename)
        chunks = split_text(text, source_id, title, origin="upload")
        if not chunks:
            raise ValueError(f"{filename} produced no chunks.")
        documents.extend(chunks)
        entries.append(
            {
                "id": source_id,
                "title": title,
                "filename": filename,
                "origin": "upload",
                "chunks": len(chunks),
            }
        )
    if not documents:
        raise ValueError("No files to index.")
    return _index_documents(documents, entries)


def main() -> None:
    result = ingest()
    print(f"Ingested {result['chunks']} chunks from {', '.join(result['sources'])}")
    print(f"Index: {result['persist']}")


if __name__ == "__main__":
    main()
