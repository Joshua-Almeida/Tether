from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

from app.graph.crag import run_crag  # noqa: E402
from app.rag.citations import parse_citation_ids  # noqa: E402
from app.rag.store import retrieve  # noqa: E402


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


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Tether retrieval and refuse evals")
    parser.add_argument("--skip-llm", action="store_true", help="retrieval-only; skip ask/refuse")
    args = parser.parse_args()
    gold = json.loads((Path(__file__).parent / "gold.json").read_text(encoding="utf-8"))

    retrieval_scores = []
    for row in gold["retrieval"]:
        hit = retrieval_hit(row["question"], row["must_sources"])
        retrieval_scores.append(hit)
        print(f"retrieval {'HIT ' if hit else 'MISS'} {row['id']}")

    recall = sum(retrieval_scores) / len(retrieval_scores)
    print(f"retrieval recall@k (source): {recall:.2f}")

    if args.skip_llm:
        return

    faith_scores = []
    refuse_scores = []
    for row in gold["retrieval"]:
        state = run_crag(row["question"])
        ok = state.get("decision") == "answer" and citation_precision(
            state.get("answer") or "", state.get("citations") or []
        ) == 1.0
        faith_scores.append(ok)
        print(f"faith/cite {'PASS' if ok else 'FAIL'} {row['id']} -> {state.get('decision')}")

    for row in gold["refuse"]:
        state = run_crag(row["question"])
        ok = state.get("decision") == "refuse"
        refuse_scores.append(ok)
        print(f"refuse     {'PASS' if ok else 'FAIL'} {row['id']} -> {state.get('decision')}")

    print(f"citation-precision+answer: {sum(faith_scores) / len(faith_scores):.2f}")
    print(f"refuse accuracy:           {sum(refuse_scores) / len(refuse_scores):.2f}")


if __name__ == "__main__":
    main()
