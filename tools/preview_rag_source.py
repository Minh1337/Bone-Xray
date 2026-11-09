"""Preview a local public-text source without changing the active RAG corpus."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
from urllib.parse import urlparse

from rag import build_corpus as corpus


def preview(source_path, payload_path, output):
    source_path, payload_path, output = map(Path, (source_path, payload_path, output))
    output = output.resolve()
    if output.exists():
        raise ValueError("Preview directory already exists; choose a new directory")
    for active in (corpus.DATA, corpus.CACHE, corpus.ROOT / "index", corpus.ROOT / "models"):
        if output.is_relative_to(active.resolve()):
            raise ValueError("Preview must be outside active RAG data/cache/index/model directories")
    source = json.loads(source_path.read_text(encoding="utf-8"))
    if not isinstance(source, dict):
        raise ValueError("Source declaration must be one JSON object")
    for key in ("id", "title", "url", "license", "license_url", "scope"):
        if not isinstance(source.get(key), str) or not source[key].strip():
            raise ValueError(f"Source requires nonempty field: {key}")
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", source["id"]):
        raise ValueError("Source id must use lowercase letters/digits and hyphens")
    corpus.validate_source(source)
    if payload_path.stat().st_size > 5_000_000:
        raise ValueError("Source payload exceeds 5 MB")
    raw = payload_path.read_bytes()
    if not raw or len(raw) > 5_000_000:
        raise ValueError("Source payload is empty or exceeds 5 MB")
    kind = source.get("format", "html")
    if kind == "jats_xml":
        blocks, pmcid, doi = corpus.extract_jats_blocks(raw)
        if pmcid != source.get("pmcid") or doi != source.get("doi"):
            raise ValueError("JATS identity differs from source declaration")
    elif kind == "bioc_json":
        blocks, pmcid = corpus.extract_bioc_blocks(raw)
        if pmcid != source.get("pmcid"):
            raise ValueError("BioC identity differs from source declaration")
    elif kind == "nci_glossary_json":
        blocks, _ = corpus.extract_nci_glossary_blocks(raw, expected_term_id=source["nci_term_id"],
                                                     expected_term_name=source.get("nci_term_name"))
    else:
        blocks = corpus.extract_blocks(raw.decode("utf-8", errors="replace"))
    declaration = {"authors": "National Cancer Institute", "publisher": "National Cancer Institute", **source}
    if urlparse(source["url"]).hostname != "www.cancer.gov" and (not source.get("authors") or not source.get("publisher")):
        raise ValueError("Non-NCI sources require authors and publisher")
    payload_hash = hashlib.sha256(raw).hexdigest()
    timestamp = datetime.fromtimestamp(payload_path.stat().st_mtime, timezone.utc).isoformat()
    chunks = corpus.chunks_for(declaration, blocks, payload_hash, timestamp, source.get("source_date"))
    if not chunks:
        raise ValueError("No usable text extracted")
    # Serialize before creating files, so invalid metadata leaves no output.
    source_json = json.dumps(declaration, ensure_ascii=False, indent=2, allow_nan=False)
    chunks_json = "".join(json.dumps(c, ensure_ascii=False, allow_nan=False) + "\n" for c in chunks)
    result = {"status": "REVIEW_REQUIRED", "source_id": source["id"], "chunk_count": len(chunks),
              "payload_sha256": payload_hash, "declaration_sha256": hashlib.sha256(source_path.read_bytes()).hexdigest(),
              "preview_tool_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              "acquisition_time_basis": "Payload filesystem mtime; reviewer must verify actual acquisition record",
              "created_at_utc": datetime.now(timezone.utc).isoformat(),
              "active_corpus_changed": False, "answer_ready": False,
              "limitations": ["Parser/license declarations do not certify rights, relevance, or medical truth.",
                              "HTML article identity needs manual verification; extracted text may contain untrusted instructions.",
                              "No images are imported; no model is trained; nothing is automatically ingested."]}
    output.mkdir(parents=True, exist_ok=False)
    (output / "source.json").write_text(source_json + "\n", encoding="utf-8")
    (output / "chunks.jsonl").write_text(chunks_json, encoding="utf-8")
    (output / "preview.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--payload", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        print(json.dumps(preview(args.source, args.payload, args.output), ensure_ascii=False, indent=2))
    except (OSError, ValueError, KeyError, TypeError) as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    main()
