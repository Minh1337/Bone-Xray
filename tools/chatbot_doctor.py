"""Read-only local readiness checks. Never contacts an AI provider."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sqlite3


ROOT = Path(__file__).resolve().parents[1]
CORE_MODULES = ("fastapi", "uvicorn", "dotenv", "multipart", "httpx", "openai", "PIL", "numpy")
CLASSIFIER_ASSETS = ("best_model.pt", "config.json", "metadata_processor.joblib", "val_transform.json")
LFS_POINTER = b"version https://git-lfs.github.com/spec/v1"


def inspect_workspace(root=ROOT, *, module_available=None):
    root = Path(root)
    available = module_available or (lambda name: importlib.util.find_spec(name) is not None)
    checks = []

    def add(name, status, detail):
        checks.append({"name": name, "status": status, "detail": detail})

    missing = [name for name in CORE_MODULES if not available(name)]
    add("dependencies", "ERROR" if missing else "PASS",
        "Missing: " + ", ".join(missing) if missing else "Core chatbot dependencies found")
    for relative in ("rag/demo_api.py", "rag/demo_web/index.html", "rag/demo_web/app.js",
                     "rag/demo_web/style.css", "rag/demo_web/studio.css", "rag/demo_web/graphite.css"):
        add(relative, "PASS" if (root / relative).is_file() else "ERROR", "Required application file")

    values = {}
    if available("dotenv"):
        from dotenv import dotenv_values
        values.update(dotenv_values(root / ".env") if (root / ".env").is_file() else {})
    values.update(os.environ)
    provider = values.get("LLM_PROVIDER", "openrouter")
    model = values.get("OPENROUTER_MODEL", "openrouter/free") or ""
    paid = values.get("OPENROUTER_PAID_FALLBACK_MODEL", "qwen/qwen3.5-flash-02-23")
    valid = provider == "openrouter" and (model == "openrouter/free" or model.endswith(":free"))
    valid = valid and paid == "qwen/qwen3.5-flash-02-23"
    add("provider_config", "PASS" if valid else "ERROR",
        "Provider/model allowlist valid" if valid else "Use OpenRouter Free primary and the configured Qwen fallback; see .env.example")
    has_key = bool((values.get("OPENROUTER_API_KEY") or "").strip())
    add("provider_key", "PASS" if has_key else "WARN",
        "Key configured (value hidden)" if has_key
        else "OPENROUTER_API_KEY missing; greetings/local history still work")

    manifest_path = root / "rag/index/manifest.json"
    if manifest_path.is_file():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            for key, relative in (("corpus_sha256", "rag/data/corpus.jsonl"),
                                  ("source_lock_sha256", "rag/data/source_lock.json"),
                                  ("vectors_sha256", "rag/index/vectors.npy")):
                target = root / relative
                actual = hashlib.sha256(target.read_bytes()).hexdigest() if target.is_file() else None
                if not isinstance(manifest.get(key), str) or actual != manifest[key]:
                    raise ValueError("Index inputs differ")
            add("rag_index", "PASS", "Corpus, source lock and vectors match index manifest")
        except (ValueError, KeyError, OSError):
            add("rag_index", "WARN", "Index missing/changed inputs; rebuild index before document lookup")
    else:
        add("rag_index", "WARN", "No local index; see docs/guides/README_RAG_INDEX_VI.md")
    embedding_ready = available("sentence_transformers") and (root / "rag/models/e5-small/modules.json").is_file()
    add("embedding", "PASS" if embedding_ready else "WARN", "Local embedding assets/dependency found" if embedding_ready
        else "Local embedding assets or sentence_transformers missing; document lookup unavailable")
    model_dir = root / "model"
    if all((model_dir / name).is_file() for name in CLASSIFIER_ASSETS):
        try:
            with (model_dir / "best_model.pt").open("rb") as checkpoint:
                pointer = checkpoint.read(len(LFS_POINTER)) == LFS_POINTER
            if pointer:
                add("local_classifier", "WARN", "Checkpoint is a Git LFS pointer. Run git lfs pull.")
            elif all(available(name) for name in ("torch", "timm", "joblib")):
                add("local_classifier", "PASS", "Local classifier assets/dependencies found")
            else:
                add("local_classifier", "WARN", "Classifier dependencies missing. Run scripts/01_setup.bat.")
        except OSError:
            add("local_classifier", "WARN", "Checkpoint could not be read. Check model/best_model.pt.")
    else:
        absent = [name for name in CLASSIFIER_ASSETS if not (model_dir / name).is_file()]
        add("local_classifier", "WARN", "Missing classifier files: " + ", ".join(absent))

    db = root / "data/chat_history.db"
    if db.is_file():
        try:
            with sqlite3.connect(db.resolve().as_uri() + "?mode=ro", uri=True, timeout=2) as connection:
                healthy = connection.execute("PRAGMA quick_check").fetchone()[0] == "ok"
            add("chat_database", "PASS" if healthy else "ERROR", "SQLite read-only integrity check completed")
        except sqlite3.Error:
            add("chat_database", "ERROR", "SQLite unreadable/locked; preserve data and check the database before startup")
    else:
        add("chat_database", "PASS", "New installation; SQLite will be created on startup")
    return {"status": "ERROR" if any(c["status"] == "ERROR" for c in checks) else
            "WARN" if any(c["status"] == "WARN" for c in checks) else "PASS",
            "scope": "local configuration/assets only; no model inference or provider request",
            "answer_ready": False, "checks": checks}


def print_checks(report):
    for check in report["checks"]:
        print(f"[{check['status']}] {check['name']}: {check['detail']}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = inspect_workspace()
    print(json.dumps(report, ensure_ascii=False, indent=2)) if args.json else print_checks(report)
    return 1 if report["status"] == "ERROR" else 0


if __name__ == "__main__":
    raise SystemExit(main())
