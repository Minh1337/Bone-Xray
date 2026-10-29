"""Recheck Stage 11 gate/cohort register references and hashes.

Structural integrity only: a PASS cannot close a clinical, rights or regulatory gate.
"""

import argparse
import csv
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / "docs" / "reference"


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for part in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(part)
    return digest.hexdigest()


def rows(path):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        return reader.fieldnames, list(reader)


def verify(record_path=REFERENCE / "stage11_gate_cohort_register_qa_20261029_v6.json"):
    record = json.loads(Path(record_path).read_text(encoding="utf-8"))
    errors = []

    def check_file(raw, expected, *, base=ROOT):
        if not isinstance(raw, str) or not raw:
            errors.append("invalid_reference_path")
            return
        path = (base / raw).resolve()
        if not path.is_relative_to(ROOT.resolve()) or not path.is_file():
            errors.append(f"missing_or_unsafe:{raw}")
        elif sha256(path) != expected:
            errors.append(f"hash_mismatch:{raw}")

    gate_record = record["gate_register"]
    cohort_record = record["cohort_register"]
    check_file(gate_record["path"], gate_record["sha256"])
    check_file(cohort_record["path"], cohort_record["sha256"])
    _, gates = rows(ROOT / gate_record["path"])
    fields, cohorts = rows(ROOT / cohort_record["path"])
    if len(gates) != gate_record["rows"] or len(gates) != 7:
        errors.append("gate_row_count_mismatch")
    if len(cohorts) != cohort_record["rows"] or len(fields) != cohort_record["columns"]:
        errors.append("cohort_shape_mismatch")
    if len({r["gate_id"] for r in gates}) != len(gates):
        errors.append("duplicate_gate_id")
    if len({r["candidate_id"] for r in cohorts}) != len(cohorts):
        errors.append("duplicate_candidate_id")
    all_open = all(r["status"] == "OPEN" for r in gates)
    if all_open != gate_record["all_open"] or any(r["status"] not in {"OPEN", "CLOSED"} for r in gates):
        errors.append("gate_status_mismatch")
    if len(gates) != len(gate_record["per_gate"]):
        errors.append("per_gate_row_count_mismatch")
    refs = 0
    for gate, saved in zip(gates, gate_record["per_gate"]):
        if gate["gate_id"] != saved["gate_id"] or gate["status"] != saved["status"]:
            errors.append(f"gate_record_mismatch:{gate['gate_id']}")
        expected_paths = [p.strip() for p in gate["prepared_artifacts"].split(";") if p.strip()]
        saved_paths = [p["path"] for p in saved["prepared_artifacts"]]
        if expected_paths != saved_paths:
            errors.append(f"prepared_list_mismatch:{gate['gate_id']}")
        for item in saved["prepared_artifacts"]:
            check_file(item["path"], item["sha256"], base=REFERENCE)
            refs += 1
    if refs != gate_record["prepared_artifact_references"] or gate_record["missing_references"]:
        errors.append("prepared_reference_count_mismatch")
    blanks = [(r["candidate_id"], f) for r in cohorts for f in fields if not (r.get(f) or "").strip()]
    if bool(blanks) != bool(cohort_record["blank_cells"]):
        errors.append("cohort_blank_cells_mismatch")
    disposition = all("NOT ELIGIBLE" in r["current_disposition"] or
                      "NOT EVALUABLE" in r["current_disposition"] for r in cohorts)
    if disposition != cohort_record["all_dispositions_not_eligible_or_not_evaluable"]:
        errors.append("cohort_disposition_mismatch")
    for item in record["cohort_screen_records"]:
        if item["candidate_id"] not in {r["candidate_id"] for r in cohorts}:
            errors.append(f"unknown_cohort_screen:{item['candidate_id']}")
        check_file(item["path"], item["sha256"])
    screen = record["supporting_literature_screen"]
    check_file(screen["path"], screen["sha256"])
    return {"status": "PASS" if not errors else "FAIL", "errors": errors,
            "gate_rows": len(gates), "gate_closed": sum(r["status"] == "CLOSED" for r in gates),
            "prepared_artifact_references_checked": refs, "cohort_rows": len(cohorts),
            "scope": "reference/hash/shape consistency only; not gate acceptance"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--record", type=Path,
                        default=REFERENCE / "stage11_gate_cohort_register_qa_20261029_v6.json")
    args = parser.parse_args()
    result = verify(args.record)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
