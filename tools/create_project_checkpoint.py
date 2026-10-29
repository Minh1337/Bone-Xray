"""Create a reproducible project checkpoint without changing Git state.

Includes tracked files present in the worktree, untracked non-ignored files,
and the explicitly authorized public-text source cache. Excludes runtime data,
virtual environments, Git metadata, and previous checkpoints.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import zipfile
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXCLUDED_PARTS = {".git", ".venv", "venv", "checkpoints", "__pycache__"}


def git(*args: str) -> bytes:
    return subprocess.run(["git", *args], cwd=ROOT, check=True, stdout=subprocess.PIPE).stdout


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def safe_rel(raw: bytes) -> Path | None:
    rel = Path(raw.decode("utf-8", errors="surrogateescape"))
    if rel.is_absolute() or ".." in rel.parts or any(part in EXCLUDED_PARTS for part in rel.parts):
        return None
    return rel


def collect_files() -> list[Path]:
    raw = git("ls-files", "--cached", "--others", "--exclude-standard", "-z")
    paths: set[Path] = set()
    for item in raw.split(b"\0"):
        if not item:
            continue
        rel = safe_rel(item)
        if rel is not None and (ROOT / rel).is_file():
            paths.add(rel)
    cache = ROOT / "rag" / "source_cache"
    if cache.exists():
        for path in cache.rglob("*"):
            if path.is_file():
                paths.add(path.relative_to(ROOT))
    return sorted(paths, key=lambda path: path.as_posix().casefold())


def verify_checkpoint(checkpoint_dir: Path) -> dict[str, object]:
    manifest_path = checkpoint_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    archive_name = manifest.get("archive")
    if not isinstance(archive_name, str) or Path(archive_name).name != archive_name:
        raise ValueError("manifest archive name is unsafe")
    archive = checkpoint_dir / archive_name
    if sha256(archive) != manifest.get("archive_sha256"):
        raise ValueError("archive SHA-256 mismatch")
    with zipfile.ZipFile(archive) as zf:
        bad_member = zf.testzip()
        if bad_member:
            raise ValueError(f"archive CRC failure: {bad_member}")
        members = set(zf.namelist())
        entries = manifest.get("files", [])
        if len(entries) != manifest.get("file_count", len(entries)):
            raise ValueError("manifest file_count mismatch")
        if members != {entry["path"] for entry in entries}:
            raise ValueError("archive members do not match manifest")
        for entry in entries:
            name = entry["path"]
            rel = Path(name)
            if rel.is_absolute() or ".." in rel.parts:
                raise ValueError(f"unsafe manifest path: {name}")
            data = zf.read(name)
            if len(data) != entry["bytes"] or hashlib.sha256(data).hexdigest() != entry["sha256"]:
                raise ValueError(f"member hash/size mismatch: {name}")
    return {"status": "PASS", "archive_sha256": manifest["archive_sha256"],
            "files_verified": len(entries), "crc": "PASS"}


def readiness_snapshot() -> dict[str, object]:
    def load_first(*names: str) -> dict[str, object]:
        for name in names:
            path = ROOT / name
            if path.is_file():
                return json.loads(path.read_text(encoding="utf-8"))
        return {}

    bundle_rel = "docs/reference/stage11_policy_rerun_20261029_cureus_abcrouting_v1"
    bundle_manifest_path = ROOT / bundle_rel / "manifest.json"
    bundle_manifest = (
        json.loads(bundle_manifest_path.read_text(encoding="utf-8"))
        if bundle_manifest_path.is_file() else {}
    )
    audit_candidates = (
        "docs/reference/stage11_integrity_audit_20261029_cureus_abcrouting_v1.json",
        "docs/reference/stage11_integrity_audit_20261029_continuation_recheck.json",
        "docs/reference/stage11_integrity_audit_20261029_continuation_v2.json",
    )
    replay_candidates = (
        "docs/reference/stage11_replay_20261029_cureus_abcrouting_v1.json",
        "docs/reference/stage11_replay_20261029_continuation_recheck.json",
        "docs/reference/stage11_replay_20261029_continuation_v2.json",
    )
    audit_rel = next((name for name in audit_candidates if (ROOT / name).is_file()), None)
    replay_rel = next((name for name in replay_candidates if (ROOT / name).is_file()), None)
    audit = load_first(*(audit_candidates))
    replay = load_first(*(replay_candidates))
    gates_path = ROOT / "docs/reference/stage11_acceptance_gate_status_20261029.csv"
    gates = []
    if gates_path.is_file():
        import csv
        with gates_path.open(encoding="utf-8-sig", newline="") as stream:
            gates = list(csv.DictReader(stream))
    audit_status = audit.get("status", "UNAVAILABLE")
    replay_status = replay.get("status", "UNAVAILABLE")
    report_count = replay.get("report_artifacts_checked", 0)
    mismatch_count = len(replay.get("preflight_mismatches", []))
    closed_count = sum(row.get("status") == "CLOSED" for row in gates)
    warnings = []
    if not audit or audit_status != "PASS":
        warnings.append(f"integrity_audit:{audit_status}")
    if not replay or replay_status != "PASS":
        warnings.append(f"deterministic_replay:{replay_status}")
    bundle_manifest_sha256 = hashlib.sha256(
        bundle_manifest_path.read_bytes()
    ).hexdigest() if bundle_manifest_path.is_file() else None
    if not bundle_manifest:
        warnings.append("current_bundle_manifest:UNAVAILABLE")
    if bundle_manifest_sha256 and audit.get("evaluation_report_manifest_sha256") != bundle_manifest_sha256:
        warnings.append("audit_bundle_manifest_mismatch")
    if bundle_manifest_sha256 and replay.get("manifest_sha256") != bundle_manifest_sha256:
        warnings.append("replay_bundle_manifest_mismatch")
    if report_count != 16:
        warnings.append(f"replay_report_count:{report_count}")
    if mismatch_count:
        warnings.append(f"replay_preflight_mismatches:{mismatch_count}")
    if len(gates) != 7:
        warnings.append(f"acceptance_gate_count:{len(gates)}")
    invalid_statuses = sorted({row.get("status", "") for row in gates} - {"OPEN", "CLOSED"})
    if invalid_statuses:
        warnings.append(f"acceptance_gate_status_values:{','.join(invalid_statuses)}")
    return {
        "readiness_metadata_check": "PASS" if not warnings else "WARNING",
        "readiness_metadata_warnings": warnings,
        "bundle": bundle_rel if bundle_manifest else None,
        "bundle_manifest_sha256": bundle_manifest_sha256,
        "audit_artifact": audit_rel if audit else None,
        "replay_artifact": replay_rel if replay else None,
        "audit_status": audit_status,
        "replay_status": replay_status,
        "replay_reports": report_count,
        "replay_preflight_mismatches": mismatch_count,
        "acceptance_gates_closed": closed_count,
        "acceptance_gates_total": len(gates),
        "answer_ready": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", help="Checkpoint directory under checkpoints/; defaults to timestamped name")
    parser.add_argument("--dry-run", action="store_true", help="List files and total bytes without writing")
    parser.add_argument("--verify-dir", help="Verify an existing checkpoint directory without modifying it")
    args = parser.parse_args()
    if args.verify_dir:
        checkpoint_dir = Path(args.verify_dir)
        if not checkpoint_dir.is_absolute():
            checkpoint_dir = ROOT / checkpoint_dir
        try:
            print(json.dumps(verify_checkpoint(checkpoint_dir), indent=2))
        except (OSError, ValueError, KeyError, zipfile.BadZipFile, json.JSONDecodeError) as exc:
            print(json.dumps({"status": "FAIL", "error": str(exc)}, indent=2))
            return 1
        return 0
    files = collect_files()
    total = sum((ROOT / path).stat().st_size for path in files)
    if args.dry_run:
        print(json.dumps({"root": str(ROOT), "files": len(files), "bytes": total,
                          "includes_source_cache": (ROOT / "rag/source_cache").exists(),
                          "excludes_virtualenv_and_prior_checkpoints": True}, indent=2))
        return 0
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    rel_out = Path(args.output_dir) if args.output_dir else Path("checkpoints") / stamp
    if rel_out.is_absolute() or ".." in rel_out.parts or not rel_out.parts or rel_out.parts[0] != "checkpoints":
        parser.error("--output-dir must be a relative directory inside checkpoints/")
    out_dir = ROOT / rel_out
    if out_dir.exists():
        parser.error(f"output directory already exists: {rel_out}")
    out_dir.mkdir(parents=True)
    archive = out_dir / "project_snapshot.zip"
    entries = []
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        for rel in files:
            path = ROOT / rel
            zf.write(path, rel.as_posix())
            entries.append({"path": rel.as_posix(), "bytes": path.stat().st_size, "sha256": sha256(path)})
    status = git("status", "--short", "--untracked-files=all").decode("utf-8", errors="replace")
    patch = git("diff", "--binary", "HEAD")
    (out_dir / "git_status.txt").write_text(status, encoding="utf-8")
    (out_dir / "changes.patch").write_bytes(patch)
    now = datetime.now(timezone.utc)
    manifest = {
        "created_at_utc": now.isoformat(),
        "local_time_ict": now.astimezone(timezone(timedelta(hours=7))).isoformat(),
        "git_head": git("rev-parse", "HEAD").decode().strip(),
        "git_branch": git("branch", "--show-current").decode().strip(),
        "archive": archive.name,
        "archive_sha256": sha256(archive),
        "file_count": len(entries),
        "total_uncompressed_bytes": total,
        "source_cache_included": (ROOT / "rag/source_cache").exists(),
        **readiness_snapshot(),
        "excluded": sorted(EXCLUDED_PARTS),
        "files": entries,
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    verification = verify_checkpoint(out_dir)
    print(json.dumps({"output": str(rel_out), "archive_sha256": manifest["archive_sha256"],
                      "file_count": len(entries), "total_uncompressed_bytes": total,
                      "verification": verification}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
