"""Compare the experimental unknown-query-token abstention gate without changing production config."""

import argparse
import copy
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from rag import retrieval as r
from rag.evaluate import run_evaluation
from rag.evidence import EvidenceVerifier


PROJECT = Path(__file__).resolve().parents[1]
EVIDENCE_CONFIG = r.DATA / "evidence_config.json"


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def safe_child(base, relative):
    relative = Path(relative)
    base = Path(base).resolve()
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError(f"Unsafe relative path: {relative}")
    resolved = (base / relative).resolve()
    if not resolved.is_relative_to(base) or not resolved.is_file():
        raise ValueError(f"Missing or out-of-root file: {relative}")
    return resolved


def metric_view(report):
    return {key: report.get(key) for key in (
        "answerable_count", "negative_count", "recall_at_k", "positive_abstention",
        "negative_abstention", "routing_accuracy", "negative_with_candidates_count",
        "positive_without_candidates_count",
    )}


def compare(bundle_path, output_path):
    bundle_path = Path(bundle_path).resolve()
    if not bundle_path.is_relative_to(PROJECT):
        raise ValueError("Bundle must be inside the project workspace")
    manifest_path = safe_child(bundle_path, "manifest.json")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    base_config = json.loads(EVIDENCE_CONFIG.read_text(encoding="utf-8"))
    candidate_config = copy.deepcopy(base_config)
    candidate_config["require_known_query_terms"] = False
    if {k: v for k, v in candidate_config.items() if k != "require_known_query_terms"} != {
        k: v for k, v in base_config.items() if k != "require_known_query_terms"
    }:
        raise AssertionError("Candidate override changed more than require_known_query_terms")
    production_config_sha256_before = sha256(EVIDENCE_CONFIG)

    engine = r.Retriever()
    engine.verifier = EvidenceVerifier(engine.corpus_rows, candidate_config)
    reports = []
    for entry in manifest["reports"]:
        if not entry.get("verify_evidence"):
            continue
        prior_path = safe_child(bundle_path, entry["path"])
        prior = json.loads(prior_path.read_text(encoding="utf-8"))
        dataset_path = safe_child(r.DATA, Path(entry["dataset_path"]).relative_to("rag/data"))
        candidate = run_evaluation(
            dataset_path,
            engine=engine,
            split=entry["split"],
            top_k=prior["top_k"],
            min_score=prior["min_score"],
            mode=entry["mode"],
            apply_policy=entry["apply_policy"],
            verify_evidence=True,
            rerank_concepts=False,
        )
        candidate["effective_checker_override"] = {
            "production_evidence_config_sha256": sha256(EVIDENCE_CONFIG),
            "field": "require_known_query_terms",
            "production_value": True,
            "candidate_value": False,
            "other_config_fields_changed": False,
        }
        reports.append({
            "report": entry["path"],
            "dataset_path": entry["dataset_path"],
            "dataset_sha256": sha256(dataset_path),
            "positive_questions": candidate["answerable_count"],
            "negative_questions": candidate["negative_count"],
            "baseline": metric_view(prior),
            "candidate": metric_view(candidate),
            "question_statuses": [
                {"id": q["id"], "answerable": q["answerable"],
                 "expected_status": q["expected_status"], "status": q["status"],
                 "reason": q["reason"], "status_match": q["status_match"],
                 "evidence_check": q.get("evidence_check")}
                for q in candidate["questions"]
            ],
        })

    positives = sum(item["positive_questions"] for item in reports)
    negatives = sum(item["negative_questions"] for item in reports)
    passed = sum(sum(q["answerable"] and q["status"] == "candidates_found"
                     for q in item["question_statuses"]) for item in reports)
    negative_candidates = sum(sum(not q["answerable"] and q["status"] == "candidates_found"
                                  for q in item["question_statuses"]) for item in reports)
    negative_abstained = negatives - negative_candidates
    production_config_sha256_after = sha256(EVIDENCE_CONFIG)
    if production_config_sha256_before != production_config_sha256_after:
        raise RuntimeError("Production evidence config changed during the in-memory experiment")
    result = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "EXPLORATORY_COMPARISON",
        "baseline_bundle": str(bundle_path),
        "baseline_manifest_sha256": sha256(manifest_path),
        "candidate_policy": "Do not reject solely because a query token is unknown; still require all recognized concepts and corpus-vocabulary literals to be covered lexically.",
        "production_config_changed": False,
        "production_evidence_config_sha256": production_config_sha256_after,
        "implementation_sha256": {
            "tools/compare_evidence_unknown_term_policy.py": sha256(Path(__file__)),
            "rag/evidence.py": sha256(r.ROOT / "evidence.py"),
            "rag/retrieval.py": sha256(r.ROOT / "retrieval.py"),
            "rag/evaluate.py": sha256(r.ROOT / "evaluate.py"),
        },
        "aggregate": {
            "strict_report_count": len(reports),
            "positive_questions": positives,
            "candidate_positive_accepts": passed,
            "positive_abstentions": positives - passed,
            "positive_abstention_rate": (positives - passed) / positives if positives else None,
            "negative_questions": negatives,
            "negative_candidate_accepts": negative_candidates,
            "negative_abstentions": negative_abstained,
            "negative_abstention_rate": negative_abstained / negatives if negatives else None,
            "interpretation": "All datasets are agent-authored or previously viewed development/regression sets. Candidate passage is lexical coverage, not citation entailment. This comparison cannot justify enabling the checker.",
        },
        "reports": reports,
    }
    output_path = Path(output_path).resolve()
    if not output_path.is_relative_to(PROJECT):
        raise ValueError("Output must be inside the project workspace")
    if output_path.exists():
        raise FileExistsError(f"Refusing to overwrite experiment report: {output_path}")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", type=Path, required=True,
                        help="Frozen evaluation bundle containing strict reports")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = compare(args.bundle, args.output)
    print(json.dumps({"status": result["status"], "aggregate": result["aggregate"],
                      "output": str(args.output)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
