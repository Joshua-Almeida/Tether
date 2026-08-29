from __future__ import annotations

import json
from typing import Any

from app.config import BACKEND_DIR
from app.rag.store import delete_by_source, sources_from_index

LIBRARY_PATH = BACKEND_DIR / "data" / "library.json"


def _empty() -> list[dict[str, Any]]:
    return []


def load_catalog() -> list[dict[str, Any]]:
    if not LIBRARY_PATH.exists():
        return _empty()
    try:
        payload = json.loads(LIBRARY_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return _empty()
    rows = payload.get("sources") if isinstance(payload, dict) else payload
    if not isinstance(rows, list):
        return _empty()
    return [row for row in rows if isinstance(row, dict) and row.get("id")]


def save_catalog(rows: list[dict[str, Any]]) -> None:
    LIBRARY_PATH.parent.mkdir(parents=True, exist_ok=True)
    LIBRARY_PATH.write_text(
        json.dumps({"sources": rows}, indent=2),
        encoding="utf-8",
    )


def upsert_catalog(entries: list[dict[str, Any]]) -> None:
    by_id = {str(row["id"]): row for row in load_catalog()}
    for entry in entries:
        by_id[str(entry["id"])] = entry
    save_catalog(sorted(by_id.values(), key=lambda row: str(row["id"])))


def drop_catalog(source_id: str) -> None:
    save_catalog([row for row in load_catalog() if str(row.get("id")) != source_id])


def remove_source(source_id: str) -> None:
    delete_by_source(source_id)
    drop_catalog(source_id)


def library_rows() -> list[dict[str, Any]]:
    catalog = {str(row["id"]): row for row in load_catalog()}
    for source_id in sources_from_index():
        if source_id not in catalog:
            catalog[source_id] = {
                "id": source_id,
                "title": source_id,
                "filename": "",
                "origin": "demo" if source_id.startswith("rfc") else "upload",
                "chunks": 0,
            }
    return sorted(catalog.values(), key=lambda row: str(row["id"]))
