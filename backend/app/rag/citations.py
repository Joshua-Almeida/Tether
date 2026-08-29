from __future__ import annotations

import re

CITATION_RE = re.compile(r"\[(\d+)\]")


def parse_citation_ids(answer: str) -> list[int]:
    ids: list[int] = []
    seen: set[int] = set()
    for match in CITATION_RE.finditer(answer or ""):
        value = int(match.group(1))
        if value not in seen:
            seen.add(value)
            ids.append(value)
    return ids


def is_refuse_text(text: str) -> bool:
    stripped = (text or "").strip().upper()
    return stripped.startswith("REFUSE") or stripped == ""


def filter_citations(answer: str, citations: list[dict]) -> list[dict]:
    allowed = set(parse_citation_ids(answer))
    return [item for item in citations if item.get("id") in allowed]


def sentences_without_citations(answer: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+", (answer or "").strip())
    missing: list[str] = []
    for part in parts:
        text = part.strip()
        if len(text) < 24:
            continue
        if not CITATION_RE.search(text):
            missing.append(text)
    return missing
