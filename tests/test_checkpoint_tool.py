import hashlib
import importlib.util
import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

TOOL_PATH = Path(__file__).resolve().parents[1] / "tools" / "create_project_checkpoint.py"
SPEC = importlib.util.spec_from_file_location("create_project_checkpoint", TOOL_PATH)
checkpoint = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(checkpoint)


class CheckpointToolTests(unittest.TestCase):
    def test_safe_rel_excludes_escape_and_runtime_paths(self):
        for path in (b"../secret.txt", b".venv/pyvenv.cfg", b"checkpoints/old/manifest.json"):
            with self.subTest(path=path):
                self.assertIsNone(checkpoint.safe_rel(path))
        self.assertEqual(checkpoint.safe_rel(b"docs/report.md"), Path("docs/report.md"))

    def test_verify_checkpoint_detects_tampered_member_manifest(self):
        payload = b"checkpoint fixture"
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            archive = directory / "project_snapshot.zip"
            with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as bundle:
                bundle.writestr("fixture.txt", payload)
            manifest = {
                "archive": archive.name,
                "archive_sha256": hashlib.sha256(archive.read_bytes()).hexdigest(),
                "file_count": 1,
                "files": [{"path": "fixture.txt", "bytes": len(payload),
                           "sha256": hashlib.sha256(payload).hexdigest()}],
            }
            manifest_path = directory / "manifest.json"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            self.assertEqual(checkpoint.verify_checkpoint(directory)["status"], "PASS")
            manifest["files"][0]["sha256"] = "0" * 64
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "member hash/size mismatch"):
                checkpoint.verify_checkpoint(directory)

    def test_readiness_metadata_fails_visible_when_inputs_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "docs" / "reference").mkdir(parents=True)
            with patch.object(checkpoint, "ROOT", root):
                result = checkpoint.readiness_snapshot()
        self.assertEqual(result["readiness_metadata_check"], "WARNING")
        self.assertIn("integrity_audit:UNAVAILABLE", result["readiness_metadata_warnings"])
        self.assertIn("deterministic_replay:UNAVAILABLE", result["readiness_metadata_warnings"])
        self.assertIn("acceptance_gate_count:0", result["readiness_metadata_warnings"])
        self.assertFalse(result["answer_ready"])

    def test_readiness_warns_when_audit_and_replay_reference_another_bundle(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            reference = root / "docs" / "reference"
            bundle = reference / "stage11_policy_rerun_20261029_cureus_abcrouting_v1"
            bundle.mkdir(parents=True)
            (bundle / "manifest.json").write_text(json.dumps({"schema_version": 2}), encoding="utf-8")
            (reference / "stage11_integrity_audit_20261029_cureus_abcrouting_v1.json").write_text(
                json.dumps({"status": "PASS", "evaluation_report_manifest_sha256": "old-bundle"}),
                encoding="utf-8",
            )
            (reference / "stage11_replay_20261029_cureus_abcrouting_v1.json").write_text(
                json.dumps({"status": "PASS", "manifest_sha256": "old-bundle",
                            "report_artifacts_checked": 16, "preflight_mismatches": []}),
                encoding="utf-8",
            )
            gates = reference / "stage11_acceptance_gate_status_20261029.csv"
            gates.write_text("gate_id,status\n" + "".join(f"G{i},OPEN\n" for i in range(1, 8)),
                             encoding="utf-8")
            with patch.object(checkpoint, "ROOT", root):
                result = checkpoint.readiness_snapshot()
        self.assertEqual(result["readiness_metadata_check"], "WARNING")
        self.assertIn("audit_bundle_manifest_mismatch", result["readiness_metadata_warnings"])
        self.assertIn("replay_bundle_manifest_mismatch", result["readiness_metadata_warnings"])
        self.assertFalse(result["answer_ready"])

    def test_current_readiness_metadata_matches_workspace(self):
        result = checkpoint.readiness_snapshot()
        self.assertEqual(result["readiness_metadata_check"], "PASS")
        self.assertEqual(result["audit_status"], "PASS")
        self.assertEqual(result["replay_status"], "PASS")
        self.assertEqual(
            result["bundle"],
            "docs/reference/stage11_policy_rerun_20261029_cureus_abcrouting_v1",
        )
        self.assertEqual(
            result["audit_artifact"],
            "docs/reference/stage11_integrity_audit_20261029_cureus_abcrouting_v1.json",
        )
        self.assertEqual(
            result["replay_artifact"],
            "docs/reference/stage11_replay_20261029_cureus_abcrouting_v1.json",
        )
        self.assertTrue(result["bundle_manifest_sha256"])
        self.assertNotIn("audit_bundle_manifest_mismatch", result["readiness_metadata_warnings"])
        self.assertNotIn("replay_bundle_manifest_mismatch", result["readiness_metadata_warnings"])
        self.assertEqual(result["replay_reports"], 16)
        self.assertEqual(result["acceptance_gates_total"], 7)
        self.assertEqual(result["acceptance_gates_closed"], 0)
        self.assertFalse(result["answer_ready"])


if __name__ == "__main__":
    unittest.main()
