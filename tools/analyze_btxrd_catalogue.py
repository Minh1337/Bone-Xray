"""Deterministic analysis of the local BTXRD reference manifest, SHA-256 duplicate groups,
22-field metadata distributions, and 10-label RAG mapping coverage (`LABEL_GUIDE`).

For educational reporting and provenance verification only (`answer_ready=False`).
"""

import argparse
import csv
import datetime
import hashlib
import json
import statistics
from pathlib import Path

from api_validation import META_COLS
from rag import case_context as cases

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "data" / "external_datasets" / "BTXRD" / "reference" / "manifest.csv"
DEFAULT_OUTPUT = ROOT / "docs" / "reference" / "stage12_btxrd_catalogue_and_mapping_analysis_20261105.json"


def analyze_manifest(manifest_path: Path = DEFAULT_MANIFEST) -> dict:
    if not manifest_path.is_file():
        raise FileNotFoundError(f"BTXRD manifest not found: {manifest_path}")

    raw_bytes = manifest_path.read_bytes()
    manifest_sha256 = hashlib.sha256(raw_bytes).hexdigest()

    rows = []
    with manifest_path.open("r", encoding="utf-8-sig", newline="") as stream:
        for row in csv.DictReader(stream):
            rows.append(row)

    total_rows = len(rows)
    by_hash: dict[str, list[dict]] = {}
    label_counts: dict[str, int] = {label: 0 for label in cases.LABEL_GUIDE}
    status_counts: dict[str, int] = {"direct": 0, "unresolved": 0, "aggregate": 0, "no_tumor": 0}
    unmapped_ground_truth_rows: list[dict] = []
    ages: list[float] = []
    gender_counts: dict[str, int] = {"M": 0, "F": 0, "other": 0}
    center_counts: dict[str, int] = {}
    center_by_label: dict[str, dict[str, int]] = {}
    site_counts: dict[str, int] = {col: 0 for col in cases.SITE_FIELDS}
    view_counts: dict[str, int] = {col: 0 for col in cases.VIEW_FIELDS}
    view_by_label: dict[str, dict[str, int]] = {
        label: {v: 0 for v in cases.VIEW_FIELDS} for label in cases.LABEL_GUIDE
    }
    demo_rule_valid_count = 0
    demo_rule_invalid_ids: list[str] = []

    for row in rows:
        gt = (row.get("ground_truth") or "").strip()
        center = str(row.get("source_center") or "unknown").strip()
        center_counts[center] = center_counts.get(center, 0) + 1
        if gt in label_counts:
            label_counts[gt] += 1
            status = cases.LABEL_GUIDE[gt]["status"]
            status_counts[status] += 1
            center_by_label.setdefault(center, {label: 0 for label in cases.LABEL_GUIDE})
            center_by_label[center][gt] += 1
        else:
            unmapped_ground_truth_rows.append({
                "image_id": row["image_id"],
                "ground_truth": gt or None,
                "ground_truth_raw": row.get("ground_truth_raw") or None,
            })

        meta = json.loads(row["metadata_json"])
        age = float(meta["age"])
        ages.append(age)
        gender = str(meta.get("gender", "")).upper()
        if gender in ("M", "F"):
            gender_counts[gender] += 1
        else:
            gender_counts["other"] += 1

        for site in cases.SITE_FIELDS:
            if int(meta.get(site, 0)) == 1:
                site_counts[site] += 1
        for view in cases.VIEW_FIELDS:
            if int(meta.get(view, 0)) == 1:
                view_counts[view] += 1
                if gt in view_by_label:
                    view_by_label[gt][view] += 1

        try:
            cases.check_demo_metadata(meta)
            demo_rule_valid_count += 1
        except ValueError:
            demo_rule_invalid_ids.append(row["image_id"])

        sha = row["sha256"].strip().lower()
        by_hash.setdefault(sha, []).append({
            "image_id": row["image_id"],
            "ground_truth": gt or None,
            "metadata": meta,
        })

    duplicate_hash_groups = []
    conflicting_metadata_groups = []
    identical_metadata_duplicate_groups = []

    for sha, entries in sorted(by_hash.items(), key=lambda item: item[1][0]["image_id"]):
        if len(entries) <= 1:
            continue
        first_meta = entries[0]["metadata"]
        same_meta = all(e["metadata"] == first_meta for e in entries[1:])
        same_gt = len({e["ground_truth"] for e in entries}) == 1
        record = {
            "sha256": sha,
            "image_ids": [e["image_id"] for e in entries],
            "ground_truths": [e["ground_truth"] for e in entries],
            "same_metadata": same_meta,
            "same_ground_truth": same_gt,
        }
        duplicate_hash_groups.append(record)
        if same_meta:
            identical_metadata_duplicate_groups.append(record)
        else:
            conflicting_metadata_groups.append(record)

    sorted_ages = sorted(ages)
    q25_idx = int(0.25 * (len(sorted_ages) - 1))
    q75_idx = int(0.75 * (len(sorted_ages) - 1))

    per_label_summary = {}
    for label, spec in cases.LABEL_GUIDE.items():
        count = label_counts.get(label, 0)
        per_label_summary[label] = {
            "count": count,
            "percentage": round(count * 100.0 / total_rows, 2) if total_rows else 0.0,
            "mapping_status": spec["status"],
            "rag_query": spec.get("query"),
            "related_query": spec.get("related_query"),
        }

    per_status_summary = {
        status: {
            "count": count,
            "percentage": round(count * 100.0 / total_rows, 2) if total_rows else 0.0,
        }
        for status, count in status_counts.items()
    }

    return {
        "record_id": "stage12-btxrd-catalogue-and-mapping-analysis-20261105",
        "created_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "scope": (
            "In-source descriptive analysis of the local BTXRD reference manifest (3,746 rows), "
            "22 metadata fields, SHA-256 duplicate-byte groups, and 10-label RAG mapping coverage. "
            "Educational and provenance documentation only; not external clinical validation."
        ),
        "answer_ready": False,
        "manifest_path": str(manifest_path.relative_to(ROOT)).replace("\\", "/"),
        "manifest_sha256": manifest_sha256,
        "total_images": total_rows,
        "unique_sha256_count": len(by_hash),
        "duplicate_sha256_Analysis": {
            "duplicate_hash_group_count": len(duplicate_hash_groups),
            "conflicting_metadata_group_count": len(conflicting_metadata_groups),
            "identical_metadata_group_count": len(identical_metadata_duplicate_groups),
            "conflicting_metadata_image_ids": sorted(
                img_id for grp in conflicting_metadata_groups for img_id in grp["image_ids"]
            ),
            "conflicting_metadata_groups": conflicting_metadata_groups,
            "identical_metadata_groups": identical_metadata_duplicate_groups,
        },
        "label_guide_coverage": {
            "mapped_single_label_count": sum(status_counts.values()),
            "unmapped_or_multilabel_count": len(unmapped_ground_truth_rows),
            "unmapped_or_multilabel_rows": unmapped_ground_truth_rows,
            "by_status": per_status_summary,
            "by_label": per_label_summary,
        },
        "metadata_distribution": {
            "columns_count": len(META_COLS),
            "age_summary": {
                "min": round(min(sorted_ages), 2),
                "q25": round(sorted_ages[q25_idx], 2),
                "median": round(statistics.median(sorted_ages), 2),
                "mean": round(statistics.mean(sorted_ages), 2),
                "stdev": round(statistics.pstdev(sorted_ages), 2),
                "q75": round(sorted_ages[q75_idx], 2),
                "max": round(max(sorted_ages), 2),
            },
            "gender_counts": gender_counts,
            "source_center_counts": dict(sorted(center_counts.items())),
            "source_center_by_label": {
                k: center_by_label[k] for k in sorted(center_by_label.keys())
            },
            "anatomical_site_positive_counts": dict(
                sorted(site_counts.items(), key=lambda kv: kv[1], reverse=True)
            ),
            "radiographic_view_positive_counts": view_counts,
            "radiographic_view_by_label": view_by_label,
            "demo_strict_rule_check": {
                "rule": ">=1 anatomical site == 1 and ==1 radiographic view == 1",
                "compliant_count": demo_rule_valid_count,
                "compliant_percentage": round(demo_rule_valid_count * 100.0 / total_rows, 2),
                "non_compliant_count": len(demo_rule_invalid_ids),
                "non_compliant_sample_ids": demo_rule_invalid_ids[:15],
            },
        },
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    report = analyze_manifest(args.manifest)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": "OK",
        "total_images": report["total_images"],
        "unique_sha256_count": report["unique_sha256_count"],
        "conflicting_metadata_group_count": report["duplicate_sha256_Analysis"]["conflicting_metadata_group_count"],
        "output": str(args.output),
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
