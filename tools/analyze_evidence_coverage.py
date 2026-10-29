#!/usr/bin/env python3
"""Reproduce per-query diagnostics for the experimental lexical evidence checker.

This inspects the dataset's already-labeled reference chunks. It does not run
retrieval, judge medical correctness, or validate entailment.
"""

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from rag.evidence import EvidenceVerifier


DEFAULT_DATASET = ROOT / "rag/data/evaluation_osteofibrous_dysplasia_dev_20261028.json"
DEFAULT_OUTPUT = ROOT / "docs/reference/stage11_evidence_verifier_miss_analysis_20261029_v2.json"


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--check", action="store_true", help="print the deterministic result without writing")
    args = parser.parse_args()

    corpus_path = ROOT / "rag/data/corpus.jsonl"
    config_path = ROOT / "rag/data/evidence_config.json"
    verifier_path = ROOT / "rag/evidence.py"
    lexical_path = ROOT / "rag/lexical.py"
    corpus = [json.loads(line) for line in corpus_path.read_text(encoding="utf-8").splitlines()]
    data = json.loads(args.dataset.read_text(encoding="utf-8"))
    by_id = {row["chunk_id"]: row for row in corpus}
    verifier = EvidenceVerifier(corpus)
    rows = []

    for question in data["questions"]:
        if question.get("expected_status") != "candidates_found":
            continue
        reference_hits = []
        for evidence in question.get("evidence", []):
            chunk_id = evidence["chunk_id"]
            row = by_id.get(chunk_id)
            if row is None:
                raise ValueError(f"Reference evidence chunk is absent from corpus: {chunk_id}")
            if row.get("text_sha256") != evidence.get("text_sha256"):
                raise ValueError(f"Reference evidence hash mismatch: {chunk_id}")
            reference_hits.append(row)

        kept, status, diagnostics = verifier.check(
            question["question_vi"], reference_hits, top_k=max(1, len(reference_hits))
        )
        rows.append({
            "question_id": question["id"],
            "question_vi": question["question_vi"],
            "reference_chunk_ids": [hit["chunk_id"] for hit in reference_hits],
            "reference_chunk_count": len(reference_hits),
            "checker_status": status,
            "kept_reference_chunks": [hit["chunk_id"] for hit in kept],
            "parsed_concepts": diagnostics["concepts"],
            "parsed_literal_terms": diagnostics["literal_terms"],
            "parsed_unknown_terms": diagnostics["unknown_terms"],
            "best_missing": diagnostics["best_missing"],
            "lexically_covered": bool(kept),
        })

    summary = {
        "artifact": "stage11_evidence_verifier_miss_analysis",
        "analysis_scope": "diagnostic_only_on_labeled_reference_chunks; no retrieval run; no independent review; no entailment or clinical-validity claim",
        "dataset": str(args.dataset.relative_to(ROOT)).replace("\\", "/"),
        "dataset_sha256": sha256(args.dataset),
        "corpus_sha256": sha256(corpus_path),
        "evidence_config_sha256": sha256(config_path),
        "checker_version": verifier.config["version"],
        "evidence_code_sha256": sha256(verifier_path),
        "lexical_code_sha256": sha256(lexical_path),
        "expected_positive_queries": len(rows),
        "lexically_covered_reference_queries": sum(row["lexically_covered"] for row in rows),
        "positive_abstentions_on_reference_chunks": sum(not row["lexically_covered"] for row in rows),
        "queries": rows,
        "interpretation": "A refusal on a known reference chunk identifies lexical coverage failure for this agent-authored in-sample query. It does not prove retrieval failure, corpus insufficiency, or a medically wrong label. Keep the optional checker disabled pending an independently authored and reviewed multilingual benchmark.",
    }
    encoded = json.dumps(summary, ensure_ascii=False, indent=2) + "\n"
    if args.check:
        print(encoded, end="")
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded, encoding="utf-8")
        print(f"Wrote {args.output.relative_to(ROOT)}")
        print(f"covered={summary['lexically_covered_reference_queries']}/{summary['expected_positive_queries']} sha256={sha256(args.output)}")


if __name__ == "__main__":
    main()
