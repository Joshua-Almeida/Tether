from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

from app.rag.citations import parse_citation_ids, sentences_without_citations  # noqa: E402
from app.rag.store import chunk_count, retrieve  # noqa: E402


def retrieval_hit(question: str, must_sources: list[str], k: int = 6) -> bool:
    docs = retrieve(question, k=k)
    found = {str(doc.metadata.get("source")) for doc in docs}
    return all(source in found for source in must_sources)


def citation_precision(answer: str, citations: list[dict]) -> float:
    cited = parse_citation_ids(answer)
    if not cited:
        return 0.0
    valid = {item["id"] for item in citations}
    return sum(1 for item in cited if item in valid) / len(cited)


def faith_ok(state: dict) -> bool:
    answer = state.get("answer") or ""
    citations = state.get("citations") or []
    if state.get("decision") != "answer":
        return False
    if citation_precision(answer, citations) != 1.0:
        return False
    return not sentences_without_citations(answer)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Tether retrieval and refuse evals")
    parser.add_argument("--skip-llm", action="store_true", help="retrieval-only; skip ask/refuse")
    args = parser.parse_args()

    if chunk_count() == 0:
        print("Index is empty. Ingest first: python -m app.ingest")
        raise SystemExit(2)

    gold = json.loads((Path(__file__).parent / "gold.json").read_text(encoding="utf-8"))

    retrieval_scores = []
    for row in gold["retrieval"]:
        hit = retrieval_hit(row["question"], row["must_sources"])
        retrieval_scores.append(hit)
        print(f"retrieval {'HIT ' if hit else 'MISS'} {row['id']}")

    recall = sum(retrieval_scores) / len(retrieval_scores)
    print(f"retrieval recall@k (source): {recall:.2f}")
    retrieval_ok = all(retrieval_scores)

    if args.skip_llm:
        raise SystemExit(0 if retrieval_ok else 1)

    from app.graph.crag import run_crag  # noqa: WPS433

    faith_scores = []
    refuse_scores = []
    for row in gold["retrieval"]:
        state = run_crag(row["question"])
        ok = faith_ok(state)
        faith_scores.append(ok)
        reason = state.get("refuse_reason") or ""
        print(
            f"faith/cite {'PASS' if ok else 'FAIL'} {row['id']} -> "
            f"{state.get('decision')} {reason}".rstrip()
        )

    for row in gold["refuse"]:
        state = run_crag(row["question"])
        ok = state.get("decision") == "refuse" and not (state.get("citations") or [])
        refuse_scores.append(ok)
        reason = state.get("refuse_reason") or ""
        print(
            f"refuse     {'PASS' if ok else 'FAIL'} {row['id']} -> "
            f"{state.get('decision')} {reason}".rstrip()
        )

    print(f"citation-precision+answer: {sum(faith_scores) / len(faith_scores):.2f}")
    print(f"refuse accuracy:           {sum(refuse_scores) / len(refuse_scores):.2f}")
    if not all(faith_scores) or not all(refuse_scores):
        print("note: LLM rows are observational. A miss is not a runner crash; see docs/STUDY.md.")
    raise SystemExit(0 if retrieval_ok else 1)


if __name__ == "__main__":
    main()
