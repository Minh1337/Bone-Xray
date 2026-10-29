"""Check that register QA detects altered evidence, not just missing files."""

import json
from pathlib import Path

from tools.verify_stage11_registers import REFERENCE, verify


def test_current_registers_match_record():
    assert verify()["status"] == "PASS"


def test_tampered_artifact_digest_is_rejected(tmp_path):
    record = json.loads((REFERENCE / "stage11_gate_cohort_register_qa_20261029_v6.json").read_text(encoding="utf-8"))
    record["gate_register"]["per_gate"][0]["prepared_artifacts"][0]["sha256"] = "0" * 64
    path = tmp_path / "altered.json"
    path.write_text(json.dumps(record), encoding="utf-8")
    result = verify(path)
    assert result["status"] == "FAIL"
    assert any(error.startswith("hash_mismatch:") for error in result["errors"])
