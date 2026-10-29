"""Replay a frozen evaluation bundle without rewriting its original reports."""

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path

try:
    from rag import retrieval as r
    from rag.evaluate import run_evaluation
except ModuleNotFoundError:
    import retrieval as r
    from evaluate import run_evaluation


PROJECT = Path(__file__).resolve().parent.parent
DEFAULT_BUNDLE = PROJECT / "docs" / "reference" / "stage11_policy_rerun_20261029_personal_image_jats_wrapper_v7"


def replay(bundle):
    bundle = Path(bundle).resolve()
    manifest = json.loads((bundle / "manifest.json").read_text(encoding="utf-8"))
    expected = {
        "corpus_sha256": r.sha256(r.CORPUS),
        "source_lock_sha256": r.sha256(r.LOCK),
        "retrieval_config_sha256": r.sha256(r.CONFIG),
        "evidence_config_sha256": r.sha256(r.DATA / "evidence_config.json"),
        "index_manifest_sha256": r.sha256(r.INDEX / "manifest.json"),
        "evaluate_sha256": r.sha256(r.ROOT / "evaluate.py"),
        "policy_sha256": r.sha256(r.ROOT / "policy.py"),
    }
    preflight_errors = [key for key, value in expected.items() if manifest.get(key) != value]
    result = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "bundle": str(bundle),
        "manifest_sha256": r.sha256(bundle / "manifest.json"),
        "replay_implementation_sha256": r.sha256(Path(__file__)),
        "preflight_mismatches": preflight_errors,
        "report_artifacts_checked": 0,
        "reports": [],
    }
    if preflight_errors:
        result["status"] = "FAIL"
        return result
    entries = manifest.get("reports")
    if (not isinstance(entries, list) or manifest.get("report_count") != len(entries)):
        result["preflight_mismatches"].append("report_manifest_count_or_schema")
        result["status"] = "FAIL"
        return result
    for entry in entries:
        if not isinstance(entry, dict) or not isinstance(entry.get("path"), str):
            result["preflight_mismatches"].append("report_manifest_entry_invalid")
            continue
        relative = Path(entry["path"])
        if relative.is_absolute() or ".." in relative.parts:
            result["preflight_mismatches"].append(f"report_path_unsafe:{entry['path']}")
            continue
        recorded_path = (bundle / relative).resolve()
        if not recorded_path.is_relative_to(bundle) or not recorded_path.is_file():
            result["preflight_mismatches"].append(f"report_missing_or_unsafe:{entry['path']}")
            continue
        expected_hash = entry.get("sha256")
        if not isinstance(expected_hash, str) or not re.fullmatch(r"[0-9a-f]{64}", expected_hash):
            result["preflight_mismatches"].append(f"report_hash_invalid:{entry['path']}")
            continue
        if r.sha256(recorded_path) != expected_hash:
            result["preflight_mismatches"].append(f"report_hash_mismatch:{entry['path']}")
            continue
        result["report_artifacts_checked"] += 1
    if result["preflight_mismatches"]:
        result["status"] = "FAIL"
        return result
    engine = r.Retriever()
    for entry in entries:
        dataset_relative = Path(entry["dataset_path"])
        report_relative = Path(entry["path"])
        if (dataset_relative.is_absolute() or ".." in dataset_relative.parts
                or report_relative.is_absolute() or ".." in report_relative.parts):
            raise ValueError("Unsafe dataset or report path in manifest")
        dataset = (PROJECT / dataset_relative).resolve()
        recorded_path = (bundle / report_relative).resolve()
        if not dataset.is_relative_to(r.DATA.resolve()) or not recorded_path.is_relative_to(bundle):
            raise ValueError("Manifest path escapes the expected directory")
        if r.sha256(dataset) != entry["dataset_sha256"]:
            raise ValueError(f"Dataset hash changed: {dataset_relative}")
        recorded = json.loads(recorded_path.read_text(encoding="utf-8"))
        produced = run_evaluation(dataset, engine=engine, split=entry["split"],
                                  mode=entry["mode"], apply_policy=entry["apply_policy"],
                                  verify_evidence=entry["verify_evidence"],
                                  rerank_concepts=entry["rerank_concepts"],
                                  top_k=recorded["top_k"], min_score=recorded["min_score"])
        recorded.pop("created_at", None)
        produced.pop("created_at", None)
        differences = sorted(key for key in set(recorded) | set(produced)
                             if recorded.get(key) != produced.get(key))
        result["reports"].append({"path": entry["path"], "match": not differences,
                                  "different_fields": differences})
    result["status"] = "PASS" if (len(result["reports"]) == manifest["report_count"]
                                   and all(item["match"] for item in result["reports"])) else "FAIL"
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", type=Path, default=DEFAULT_BUNDLE)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = replay(args.bundle)
    serialized = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(serialized, encoding="utf-8")
    print(serialized, end="")
    if result["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
