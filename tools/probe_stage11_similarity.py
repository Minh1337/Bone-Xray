"""Descriptive dense-score overlap probe on a viewed, agent-authored RAG set.

This is a research diagnostic, not a calibration procedure or release threshold.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from rag import retrieval as r


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATASET = ROOT / "rag/data/evaluation_v2.json"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    dataset = args.dataset.resolve()
    if not dataset.is_file() or not dataset.is_relative_to(ROOT):
        parser.error("dataset must be an existing file under the project")
    target = args.output.resolve() if args.output else None
    if target is not None:
        if not target.is_relative_to(ROOT):
            parser.error("output must be under the project")
        if target.exists():
            parser.error(f"output already exists: {target}; choose a new record name")
    payload = json.loads(dataset.read_text(encoding="utf-8"))
    questions = payload["questions"]
    engine = r.Retriever()
    observations = []
    for item in questions:
        question = item["question_vi"]
        # Dense top-1 is the maximum original cosine score used by min_score.
        hits = engine.search(question, top_k=1, mode="dense")
        policy = r.retrieve(question, engine=engine, top_k=5)
        observations.append({
            "id": item["id"], "split": item.get("split"),
            "expected_status": item.get("expected_status"),
            "raw_dense_top1_score": hits[0]["score"] if hits else None,
            "policy_status": policy["status"],
            "policy_hit_count": len(policy["hits"]),
        })
    positives = [x["raw_dense_top1_score"] for x in observations
                 if x["expected_status"] == "candidates_found"]
    negatives = [x["raw_dense_top1_score"] for x in observations
                 if x["expected_status"] != "candidates_found"]
    report = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "purpose": "descriptive viewed-set diagnostic; no threshold selected or deployed",
        "dataset": dataset.relative_to(ROOT).as_posix(),
        "dataset_sha256": r.sha256(dataset),
        "retrieval_sha256": r.sha256(ROOT / "rag/retrieval.py"),
        "config_sha256": r.sha256(r.CONFIG),
        "corpus_sha256": r.sha256(r.CORPUS),
        "index_manifest_sha256": r.sha256(r.INDEX / "manifest.json"),
        "model_sha256": r.sha256(r.MODEL / "model.safetensors"),
        "question_count": len(observations),
        "expected_positive_count": len(positives),
        "expected_negative_count": len(negatives),
        "positive_dense_top1_min": min(positives) if positives else None,
        "negative_dense_top1_max": max(negatives) if negatives else None,
        "score_overlap": bool(positives and negatives and max(negatives) >= min(positives)),
        "observations": observations,
        "limitations": [
            "Agent-authored and viewed dataset; not blind independent evaluation.",
            "Raw dense cosine score differs from hybrid ranking_score and does not test citation support.",
            "Policy routing can abstain independently of score; threshold-only classification is not deployed.",
        ],
    }
    output = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if target is not None:
        try:
            with target.open("x", encoding="utf-8") as stream:
                stream.write(output)
        except FileExistsError:
            parser.error(f"output already exists: {target}; choose a new record name")
        print(json.dumps({key: report[key] for key in (
            "question_count", "expected_positive_count", "expected_negative_count",
            "positive_dense_top1_min", "negative_dense_top1_max", "score_overlap")}, indent=2))
    else:
        print(output, end="")


if __name__ == "__main__":
    main()
