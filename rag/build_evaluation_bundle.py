"""Rebuild a frozen Stage 11 evaluation bundle against the current code and data."""

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

try:
    from rag import retrieval as r
    from rag.evaluate import run_evaluation
except ModuleNotFoundError:
    import retrieval as r
    from evaluate import run_evaluation


PROJECT = Path(__file__).resolve().parent.parent
DEFAULT_BASE = PROJECT / "docs" / "reference" / "stage11_policy_rerun_20261028_post_ofd"


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _safe_project_file(relative, parent):
    relative = Path(relative)
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError(f"Unsafe project-relative path: {relative}")
    resolved = (PROJECT / relative).resolve()
    if not resolved.is_relative_to(parent.resolve()):
        raise ValueError(f"Path escapes expected root: {relative}")
    return resolved


def build_bundle(base_dir, output_dir):
    base_dir = Path(base_dir).resolve()
    output_dir = Path(output_dir).resolve()
    if output_dir.exists():
        raise FileExistsError(f"Refusing to overwrite evaluation bundle: {output_dir}")
    if not base_dir.is_dir():
        raise FileNotFoundError(f"Base evaluation bundle missing: {base_dir}")

    base_manifest_path = base_dir / "manifest.json"
    base_manifest = json.loads(base_manifest_path.read_text(encoding="utf-8"))
    if base_manifest.get("schema_version") != 2:
        raise ValueError("Expected schema_version 2 evaluation manifest")
    if base_manifest.get("report_count") != len(base_manifest.get("reports", [])):
        raise ValueError("Base manifest report count is inconsistent")

    output_dir.mkdir(parents=True)
    engine = r.Retriever()
    report_entries = []
    comparison_entries = []
    current_hashes = {
        "corpus_sha256": sha256(r.CORPUS),
        "source_lock_sha256": sha256(r.LOCK),
        "retrieval_config_sha256": sha256(r.CONFIG),
        "evidence_config_sha256": sha256(r.DATA / "evidence_config.json"),
        "index_manifest_sha256": sha256(r.INDEX / "manifest.json"),
        "evaluate_sha256": sha256(r.ROOT / "evaluate.py"),
        "policy_sha256": sha256(r.ROOT / "policy.py"),
    }

    for entry in base_manifest["reports"]:
        dataset_path = _safe_project_file(entry["dataset_path"], r.DATA)
        old_report_path = (base_dir / entry["path"]).resolve()
        if not old_report_path.is_relative_to(base_dir) or not old_report_path.is_file():
            raise ValueError(f"Unsafe or missing base report: {entry['path']}")
        old_report = json.loads(old_report_path.read_text(encoding="utf-8"))
        report = run_evaluation(
            dataset_path,
            engine=engine,
            split=entry["split"],
            top_k=old_report["top_k"],
            min_score=old_report["min_score"],
            mode=entry["mode"],
            apply_policy=entry["apply_policy"],
            verify_evidence=entry["verify_evidence"],
            rerank_concepts=entry["rerank_concepts"],
        )
        relative_report = Path(entry["path"])
        if relative_report.is_absolute() or ".." in relative_report.parts:
            raise ValueError(f"Unsafe report output path: {relative_report}")
        new_report_path = output_dir / relative_report
        write_json(new_report_path, report)
        current_entry = {
            "path": relative_report.as_posix(),
            "sha256": sha256(new_report_path),
            "dataset_path": entry["dataset_path"],
            "dataset_sha256": sha256(dataset_path),
            "corpus_sha256": report["corpus_sha256"],
            "source_lock_sha256": report["source_lock_sha256"],
            "config_sha256": report["config_sha256"],
            "evidence_config_sha256": report.get("evidence_config_sha256"),
            "index_manifest_sha256": report["index_manifest_sha256"],
            "evaluate_sha256": report["implementation_sha256"]["evaluate.py"],
            "policy_sha256": report["implementation_sha256"]["policy.py"],
            "mode": report["mode"],
            "apply_policy": report["apply_policy"],
            "verify_evidence": report["verify_evidence"],
            "rerank_concepts": report["rerank_concepts"],
            "split": report["split"],
            "question_count": len(report["questions"]),
        }
        prior_metrics = entry.get("metrics", {})
        current_metrics = {key: report.get(key) for key in prior_metrics}
        current_entry["metrics"] = current_metrics
        report_entries.append(current_entry)
        metrics_changed = {
            key: {"previous": value, "current": current_metrics.get(key)}
            for key, value in prior_metrics.items()
            if value != current_metrics.get(key)
        }
        comparison_entries.append({
            "report": relative_report.as_posix(),
            "dataset_sha256_previous": entry["dataset_sha256"],
            "dataset_sha256_current": current_entry["dataset_sha256"],
            "question_count_previous": entry.get("question_count"),
            "question_count_current": len(report["questions"]),
            "changed_metrics": metrics_changed,
        })

    comparison = {
        "schema_version": 1,
        "previous_snapshot": base_dir.name,
        "current_snapshot": output_dir.name,
        "comparison_scope": (
            "All reports regenerated against current code and current datasets using the prior bundle's "
            "evaluation configuration. Agent-authored development probes are in-sample and not independent."
        ),
        "reports": comparison_entries,
    }
    comparison_path = output_dir / "comparison.json"
    write_json(comparison_path, comparison)

    manifest = {
        "schema_version": 2,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        **current_hashes,
        "report_count": len(report_entries),
        "reports": report_entries,
        "comparison": {
            "path": "comparison.json",
            "sha256": sha256(comparison_path),
            "reports_compared": len(comparison_entries),
        },
    }
    write_json(output_dir / "manifest.json", manifest)
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", type=Path, default=DEFAULT_BASE)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = build_bundle(args.base, args.output)
    print(json.dumps({
        "status": "BUILT",
        "bundle": str(Path(args.output).resolve()),
        "report_count": result["report_count"],
        "manifest_sha256": sha256(Path(args.output).resolve() / "manifest.json"),
        "comparison_sha256": result["comparison"]["sha256"],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
