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


def _pdf_text(data: bytes) -> str:
    from pypdf import PdfReader
    from pypdf.errors import FileNotDecryptedError, PdfReadError

    try:
        reader = PdfReader(io.BytesIO(data), strict=False)
    except PdfReadError as exc:
        raise ValueError(f"Could not open that PDF. {exc}") from exc
    except Exception as exc:
        raise ValueError(f"Could not open that PDF. {exc}") from exc

    if getattr(reader, "is_encrypted", False):
        try:
            reader.decrypt("")
        except Exception as exc:
            raise ValueError("That PDF is password-protected.") from exc

    pages: list[str] = []
    for page in reader.pages:
        try:
            part = page.extract_text() or ""
        except (PdfReadError, FileNotDecryptedError, KeyError, TypeError, ValueError):
            part = ""
        if part.strip():
            pages.append(part.strip())
    text = "\n\n".join(pages)
    if not text.strip():
        raise ValueError(
            "No text could be read from that PDF. Use a text-based PDF, not a scanned image."
        )
    return text


def extract_text(filename: str, data: bytes) -> str:
    suffix = Path(filename).suffix.lower()
    if suffix not in ALLOWED:
        raise ValueError("Use a PDF, .txt, or Markdown file.")
    if suffix in {".txt", ".md", ".markdown"}:
        text = data.decode("utf-8", errors="replace")
        if not text.strip():
            raise ValueError(f"{filename} is empty.")
        return text
    return _pdf_text(data)
