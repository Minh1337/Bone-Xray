"""Prepare/sweep a retrieval score threshold; never changes runtime policy.

Labels and acceptance criteria must be supplied by the study owner/reviewers.
The held-out split is evaluated once at the threshold selected on calibration.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BINDINGS = {"corpus": "rag/data/corpus.jsonl", "source_lock": "rag/data/source_lock.json",
            "config": "rag/data/retrieval_config.json", "index": "rag/index/manifest.json",
            "retrieval": "rag/retrieval.py", "policy": "rag/policy.py"}
POPULATIONS = ("fully_answerable", "partially_answerable", "in_scope_unanswerable", "out_of_scope")


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def bindings(root=ROOT):
    return {name: sha256(Path(root) / relative) for name, relative in BINDINGS.items()}


def template(root=ROOT):
    return {"schema_version": 1, "purpose": "reviewer_supplied",
            "independence": "Requires external review; not verified by this software",
            "bindings": bindings(root),
            "criteria": {"min_fully_answerable_retention": None,
                         "max_unsupported_candidate_rate": None},
            "questions": [],
            "question_fields": ["id", "cluster_id", "split (calibration or holdout)", "question_vi",
                                "answerability (answerable, partially_answerable, unanswerable)",
                                "expected_status (candidates_found, insufficient_evidence, out_of_scope)"],
            "notes": "Owner/reviewers supply labels/criteria before seeing ranks/scores. Do not paste patient data."}


def validate_dataset(dataset, current_bindings):
    if dataset.get("schema_version") != 1 or dataset.get("bindings") != current_bindings:
        raise ValueError("Dataset schema or frozen corpus/index/config/code bindings do not match")
    if dataset.get("purpose") not in {"development", "reviewer_supplied"}:
        raise ValueError("Dataset purpose must be development or reviewer_supplied")
    rows = dataset.get("questions")
    if not isinstance(rows, list):
        raise ValueError("questions must be a list")
    ids, texts, clusters = set(), {}, {}
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("Each question must be an object")
        for key in ("id", "cluster_id", "question_vi"):
            if not isinstance(row.get(key), str) or not row[key].strip():
                raise ValueError(f"Missing nonempty question field: {key}")
        if len(row["question_vi"]) > 1000 or row["id"] in ids:
            raise ValueError("Question too long or duplicate question ID")
        ids.add(row["id"])
        split = row.get("split")
        if split not in {"calibration", "holdout"}:
            raise ValueError("Every question needs calibration or holdout split")
        text = " ".join(row["question_vi"].casefold().split())
        if text in texts:
            raise ValueError("Duplicate normalized question text; do not count it twice")
        texts[text] = split
        group = row["cluster_id"]
        if group in clusters and clusters[group] != split:
            raise ValueError("A question cluster crosses calibration/holdout splits")
        clusters[group] = split
        statuses = {"answerable": {"candidates_found"},
                    "partially_answerable": {"insufficient_evidence"},
                    "unanswerable": {"insufficient_evidence", "out_of_scope"}}
        if row.get("expected_status") not in statuses.get(row.get("answerability"), set()):
            raise ValueError("Missing/inconsistent answerability and expected_status labels")
    if rows and not any(row["split"] == "calibration" for row in rows):
        raise ValueError("At least one calibration question is required before holdout evaluation")
    criteria = dataset.get("criteria", {})
    names = ("min_fully_answerable_retention", "max_unsupported_candidate_rate")
    if not isinstance(criteria, dict) or set(criteria) != set(names):
        raise ValueError("Both criteria fields are required; leave both null until owner decision")
    if any(criteria[n] is None for n in names):
        if not all(criteria[n] is None for n in names):
            raise ValueError("Supply both criteria together, or leave both null")
    elif any(isinstance(criteria[n], bool) or not isinstance(criteria[n], (int, float))
             or not math.isfinite(criteria[n]) or not 0 <= criteria[n] <= 1 for n in names):
        raise ValueError("Criteria must be finite rates between 0 and 1")
    return rows, criteria


def population(row):
    if row["expected_status"] == "out_of_scope":
        return "out_of_scope"
    return {"answerable": "fully_answerable", "partially_answerable": "partially_answerable",
            "unanswerable": "in_scope_unanswerable"}[row["answerability"]]


def metrics(rows, threshold):
    groups = {name: {"total": 0, "above_threshold": 0, "below_threshold": 0} for name in POPULATIONS}
    for row in rows:
        group = groups[population(row)]
        above = row["dense_top1_score"] >= threshold
        group["total"] += 1
        group["above_threshold" if above else "below_threshold"] += 1
    positive = groups["fully_answerable"]
    unsupported = [groups[n] for n in ("partially_answerable", "in_scope_unanswerable")]
    negative_count = sum(g["total"] for g in unsupported)
    false_candidates = sum(g["above_threshold"] for g in unsupported)
    return {"threshold": threshold, "populations": groups,
            "fully_answerable_retention": positive["above_threshold"] / positive["total"] if positive["total"] else None,
            "unsupported_candidate_rate": false_candidates / negative_count if negative_count else None,
            "tp": positive["above_threshold"], "fn": positive["below_threshold"],
            "fp": false_candidates, "tn": negative_count - false_candidates}


def analyze(rows, criteria):
    """Operate on frozen scores; only calibration rows influence selection."""
    if not rows:
        return {"status": "AWAITING_LABELS", "candidate_threshold": None, "curve": []}
    for row in rows:
        score = row.get("dense_top1_score")
        if isinstance(score, bool) or not isinstance(score, (int, float)) or not math.isfinite(score) or not -1.0001 <= score <= 1.0001:
            raise ValueError("Every observation needs a finite dense cosine score")
    calibration = [r for r in rows if r["split"] == "calibration"]
    holdout = [r for r in rows if r["split"] == "holdout"]
    counts = {s: dict(Counter(population(r) for r in rows if r["split"] == s)) for s in ("calibration", "holdout")}
    in_scope = [r for r in calibration if population(r) != "out_of_scope"]
    if not in_scope or not counts["calibration"].get("fully_answerable") or not any(
            counts["calibration"].get(n) for n in ("partially_answerable", "in_scope_unanswerable")):
        return {"status": "INSUFFICIENT_CALIBRATION_POPULATIONS", "candidate_threshold": None,
                "populations": counts, "curve": []}
    scores = {r["dense_top1_score"] for r in in_scope}
    thresholds = sorted(scores | {math.nextafter(max(scores), math.inf)})
    curve = [metrics(calibration, value) for value in thresholds]
    base = {"populations": counts, "curve": curve, "candidate_threshold": None,
            "selection_rule": "Maximize calibration retention, then minimize unsupported candidate rate, then prefer higher threshold; never tune on holdout"}
    if criteria["min_fully_answerable_retention"] is None:
        return {**base, "status": "AWAITING_CRITERIA"}
    feasible = [m for m in curve if m["fully_answerable_retention"] >= criteria["min_fully_answerable_retention"]
                and m["unsupported_candidate_rate"] <= criteria["max_unsupported_candidate_rate"]]
    if not feasible:
        return {**base, "status": "NO_FEASIBLE_THRESHOLD"}
    selected = max(feasible, key=lambda m: (m["fully_answerable_retention"], -m["unsupported_candidate_rate"], m["threshold"]))
    enough_holdout = counts["holdout"].get("fully_answerable") and any(
        counts["holdout"].get(n) for n in ("partially_answerable", "in_scope_unanswerable"))
    return {**base, "status": "CANDIDATE_REQUIRES_REVIEW" if enough_holdout else "CALIBRATION_ONLY",
            "candidate_threshold": selected["threshold"], "calibration_metrics": selected,
            "holdout_metrics": metrics(holdout, selected["threshold"]) if holdout else None,
            "holdout_criteria_met": (metrics(holdout, selected["threshold"])["fully_answerable_retention"] >= criteria["min_fully_answerable_retention"]
                                     and metrics(holdout, selected["threshold"])["unsupported_candidate_rate"] <= criteria["max_unsupported_candidate_rate"])
            if enough_holdout else None}


def run(dataset_path, *, root=ROOT, engine=None):
    dataset_path = Path(dataset_path)
    dataset = json.loads(dataset_path.read_text(encoding="utf-8"))
    frozen = bindings(root)
    rows, criteria = validate_dataset(dataset, frozen)
    observations = []
    if rows:
        from rag.retrieval import Retriever
        engine = engine or Retriever()
        def score_rows(selected):
            scored = []
            for row in selected:
                hits = engine.search(row["question_vi"], top_k=1, mode="dense")
                if not hits:
                    raise ValueError("Dense search returned no scores; verify the index")
                scored.append({**row, "dense_top1_score": hits[0]["score"]})
            return scored

        observations = score_rows(row for row in rows if row["split"] == "calibration")
        calibration_result = analyze(observations, criteria)
        # Do not reveal holdout scores until criteria are supplied and a
        # threshold has actually been selected without using those scores.
        if calibration_result["candidate_threshold"] is not None:
            observations.extend(score_rows(row for row in rows if row["split"] == "holdout"))
    return {"created_at_utc": datetime.now(timezone.utc).isoformat(), "schema_version": 1,
            "purpose": dataset["purpose"], "independence_verified": False,
            "dataset_sha256": sha256(dataset_path), "bindings": frozen,
            "tool_sha256": sha256(Path(__file__)), "criteria": criteria,
            "score_definition": "Maximum original dense cosine; not hybrid ranking_score or answer correctness",
            **analyze(observations, criteria), "observations": observations,
            "holdout_scored": any(row["split"] == "holdout" for row in observations),
            "withheld_holdout_count": sum(row["split"] == "holdout" for row in rows)
            - sum(row["split"] == "holdout" for row in observations),
            "runtime_policy_changed": False, "answer_ready": False,
            "limitations": ["Reviewer independence/label correctness cannot be certified by this tool.",
                            "Exact duplicate/cluster overlap checks do not detect all paraphrases or leakage.",
                            "Counts/rates are descriptive; cluster uncertainty, sample-size adequacy and evidence support need external review.",
                            "Out-of-scope questions are reported separately, excluded from selection; runtime policy guards remain necessary.",
                            "No threshold is installed; G1-G7 remain OPEN."]}


def write_new(path, payload):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as stream:
        json.dump(payload, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write("\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--init", action="store_true", help="Write a blank reviewer dataset bound to current artifacts")
    parser.add_argument("--dataset", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.init == bool(args.dataset):
        parser.error("Choose --init or --dataset")
    try:
        if args.output.exists():
            raise ValueError("Output already exists; choose a new report name")
        report = template() if args.init else run(args.dataset)
        write_new(args.output, report)
    except (ValueError, OSError, TypeError, KeyError) as exc:
        parser.error(str(exc))
    print(json.dumps({"output": str(args.output), "status": report.get("status", "BLANK_TEMPLATE_CREATED"),
                      "runtime_policy_changed": False, "answer_ready": False}, ensure_ascii=False))


if __name__ == "__main__":
    main()
