from __future__ import annotations

import io
import re
from pathlib import Path

ALLOWED = {".pdf", ".txt", ".md", ".markdown"}


def source_id_for(filename: str) -> str:
    stem = Path(filename).stem.lower()
    slug = re.sub(r"[^a-z0-9]+", "-", stem).strip("-")[:48]
    return slug or "document"


def title_for(filename: str) -> str:
    stem = Path(filename).stem.replace("_", " ").replace("-", " ").strip()
    return stem or "Untitled document"


def extract_text(filename: str, data: bytes) -> str:
    suffix = Path(filename).suffix.lower()
    if suffix not in ALLOWED:
        raise ValueError("Use a PDF, .txt, or Markdown file.")
    if suffix in {".txt", ".md", ".markdown"}:
        return data.decode("utf-8", errors="replace")
    from pypdf import PdfReader

    reader = PdfReader(io.BytesIO(data))
    pages = [(page.extract_text() or "").strip() for page in reader.pages]
    text = "\n\n".join(part for part in pages if part)
    if not text.strip():
        raise ValueError("That PDF has no extractable text. Try a text-based PDF, not a scan.")
    return text
