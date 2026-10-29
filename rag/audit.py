"""Audit RAG provenance and persisted artifacts without loading the embedder."""

import argparse
import hashlib
import json
import math
import re
from pathlib import Path

import numpy as np

try:
    from rag.build_corpus import CACHE as DEFAULT_CACHE, validate_source
    from rag.retrieval import MODEL_ID, MODEL_REVISION, MODEL as DEFAULT_MODEL_DIR
except ModuleNotFoundError:
    from build_corpus import CACHE as DEFAULT_CACHE, validate_source
    from retrieval import MODEL_ID, MODEL_REVISION, MODEL as DEFAULT_MODEL_DIR


ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
INDEX = ROOT / "index"
DEFAULT_REPORT_DIR = (ROOT.parent / "docs" / "reference" /
                      "stage11_policy_rerun_20261029_personal_image_jats_wrapper_v7")


def _read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit(data_dir=DATA, index_dir=INDEX, model_dir=DEFAULT_MODEL_DIR, cache_dir=DEFAULT_CACHE,
          report_dir=None):
    """Return an integrity report; a clean report does not validate medical claims."""
    data_dir, index_dir, model_dir, cache_dir = (Path(data_dir), Path(index_dir),
                                                  Path(model_dir), Path(cache_dir))
    errors = []
    sources_path, lock_path, corpus_path = (data_dir / name for name in
                                            ("sources.json", "source_lock.json", "corpus.jsonl"))
    sources = _read_json(sources_path)
    locked_sources = _read_json(lock_path)
    rows = [json.loads(line) for line in corpus_path.read_text(encoding="utf-8").splitlines() if line]
    source_ids = [item["id"] for item in sources]
    lock_ids = [item["id"] for item in locked_sources]
    row_ids = [row.get("chunk_id") for row in rows]
    row_by_id = {row.get("chunk_id"): row for row in rows}
    lock_by_id = {item["id"]: item for item in locked_sources}
    if len(source_ids) != len(set(source_ids)):
        errors.append("duplicate_source_ids")
    if len(lock_ids) != len(set(lock_ids)):
        errors.append("duplicate_locked_source_ids")
    if set(source_ids) != set(lock_ids):
        errors.append("sources_and_source_lock_ids_mismatch")
    source_by_id = {item["id"]: item for item in sources}
    source_cache_checked = []
    source_cache_missing = []
    for source in sources:
        suffix = {"bioc_json": ".json", "jats_xml": ".xml",
                  "nci_glossary_json": ".json"}.get(source.get("format"), ".html")
        cached_payload = cache_dir / f"{source['id']}{suffix}"
        if not cached_payload.is_file():
            source_cache_missing.append(source["id"])
            continue
        source_cache_checked.append(source["id"])
        locked = lock_by_id.get(source["id"])
        if locked and _sha256(cached_payload) != locked.get("source_sha256"):
            errors.append(f"source_cache_payload_hash_mismatch:{source['id']}")
    config_path = data_dir / "retrieval_config.json"
    retrieval_config_hash = _sha256(config_path) if config_path.is_file() else None
    if config_path.is_file():
        config = _read_json(config_path)
        route_ids = [route.get("source_id") for route in config.get("source_routes", [])]
        if len(route_ids) != len(set(route_ids)):
            errors.append("duplicate_source_route_ids")
        for route in config.get("source_routes", []):
            source_id = route.get("source_id")
            if source_id not in source_by_id:
                errors.append(f"unknown_source_route:{source_id}")
            if not route.get("terms") or any(not isinstance(term, str) or not term.strip()
                                              for term in route.get("terms", [])):
                errors.append(f"invalid_source_route_terms:{source_id}")
        overview_cues = config.get("overview_cues", [])
        if any(not isinstance(cue, str) or not cue.strip() for cue in overview_cues):
            errors.append("invalid_overview_route_cues")
    for source_id in set(source_ids) & set(lock_ids):
        try:
            validate_source(source_by_id[source_id])
        except (KeyError, ValueError) as exc:
            errors.append(f"source_validation_failed:{source_id}:{exc}")
        for key in ("title", "url", "download_url", "format", "authors", "publisher",
                    "source_date", "doi", "pmcid", "license", "license_url", "scope"):
            if key in source_by_id[source_id] and source_by_id[source_id][key] != lock_by_id[source_id].get(key):
                errors.append(f"source_declaration_changed:{source_id}:{key}")
        source_hash = lock_by_id[source_id].get("source_sha256")
        if not isinstance(source_hash, str) or not re.fullmatch(r"[0-9a-f]{64}", source_hash):
            errors.append(f"source_payload_hash_invalid:{source_id}")
    if len(row_ids) != len(set(row_ids)):
        errors.append("duplicate_chunk_ids")

    chunk_counts = {}
    by_hash = {}
    for row in rows:
        source_id = row.get("source_id")
        locked = lock_by_id.get(source_id)
        if locked is None:
            errors.append(f"unknown_chunk_source:{row.get('chunk_id')}")
            continue
        chunk_counts[source_id] = chunk_counts.get(source_id, 0) + 1
        text_hash = hashlib.sha256(row.get("text", "").encode("utf-8")).hexdigest()
        if text_hash != row.get("text_sha256"):
            errors.append(f"chunk_text_hash_mismatch:{row.get('chunk_id')}")
        by_hash.setdefault(text_hash, []).append(row)
        for key in ("title", "url", "authors", "publisher", "license", "license_url", "scope",
                    "source_date", "accessed_at", "source_sha256", "doi", "pmcid"):
            if row.get(key, "") != locked.get(key, ""):
                error = "chunk_source_payload_hash_mismatch" if key == "source_sha256" else "chunk_source_metadata_mismatch"
                errors.append(f"{error}:{row.get('chunk_id')}:{key}")
    for source_id, locked in lock_by_id.items():
        if chunk_counts.get(source_id, 0) != locked.get("chunk_count"):
            errors.append(f"source_chunk_count_mismatch:{source_id}")

    corpus_hash, lock_hash = _sha256(corpus_path), _sha256(lock_path)
    evidence_sets = []
    evaluation_dataset_hashes = set()
    evaluation_dataset_by_hash = {}
    for path in sorted(data_dir.glob("evaluation*.json")):
        name = path.name
        dataset = _read_json(path)
        dataset_hash = _sha256(path)
        evaluation_dataset_hashes.add(dataset_hash)
        questions = dataset.get("questions", []) if isinstance(dataset, dict) else dataset
        evaluation_dataset_by_hash[dataset_hash] = questions
        if isinstance(dataset, dict) and dataset.get("corpus_sha256") != corpus_hash:
            errors.append(f"evaluation_corpus_hash_mismatch:{name}")
        for question in questions:
            evidence_rows = []
            if "evidence" in question and "evidence_groups" in question:
                errors.append(f"evaluation_evidence_schema_conflict:{name}:{question.get('id')}")
            if "evidence_groups" in question:
                groups = question["evidence_groups"]
                if (not isinstance(groups, list) or not groups
                        or any(not isinstance(group, list) or not group for group in groups)):
                    errors.append(f"evaluation_evidence_groups_invalid:{name}:{question.get('id')}")
                    groups = []
            else:
                legacy_evidence = question.get("evidence", [])
                groups = [legacy_evidence] if legacy_evidence else []
            for group in groups:
                group_keys = []
                for evidence in group:
                    if not isinstance(evidence, dict) or not all(
                            key in evidence for key in ("chunk_id", "source_id", "section", "text_sha256")):
                        errors.append(f"evaluation_evidence_metadata_missing:{name}:{question.get('id')}")
                        continue
                    if any(not isinstance(evidence[key], str) or not evidence[key].strip()
                           for key in ("chunk_id", "source_id", "section", "text_sha256")):
                        errors.append(f"evaluation_evidence_metadata_invalid:{name}:{question.get('id')}")
                        continue
                    evidence_key = (evidence["chunk_id"], evidence["source_id"],
                                    evidence["section"], evidence["text_sha256"])
                    if evidence_key in group_keys:
                        errors.append(f"evaluation_evidence_duplicate_within_group:{name}:{question.get('id')}")
                    group_keys.append(evidence_key)
                    matches = by_hash.get(evidence.get("text_sha256"), [])
                    if not matches:
                        errors.append(f"evaluation_evidence_missing:{name}:{question.get('id')}")
                        continue
                    row = next((candidate for candidate in matches if
                                candidate.get("chunk_id") == evidence.get("chunk_id")), None)
                    if row is None:
                        errors.append(f"evaluation_evidence_chunk_id_mismatch:{name}:{question.get('id')}")
                        continue
                    if (row.get("source_id"), row.get("section")) != (
                            evidence.get("source_id"), evidence.get("section")):
                        errors.append(f"evaluation_evidence_metadata_mismatch:{name}:{question.get('id')}")
                        continue
                    evidence_rows.append(row)
            quote = question.get("evidence_quote")
            if quote and evidence_rows and not any(quote in row.get("text", "") for row in evidence_rows):
                errors.append(f"evaluation_quote_missing:{name}:{question.get('id')}")
        evidence_sets.append(name)

    manifest_path, vectors_path = index_dir / "manifest.json", index_dir / "vectors.npy"
    manifest_hash = None
    vector_shape = None
    model_hash = None
    if not manifest_path.is_file() or not vectors_path.is_file():
        errors.append("index_artifact_missing")
    else:
        manifest = _read_json(manifest_path)
        manifest_hash = _sha256(manifest_path)
        if manifest.get("schema_version") != 2:
            errors.append("unsupported_index_schema")
        if (manifest.get("embedding_input") != "passage: {section}\n{text}"
                or manifest.get("normalized") is not True):
            errors.append("index_embedding_contract_mismatch")
        if manifest.get("model_id") != MODEL_ID or manifest.get("model_revision") != MODEL_REVISION:
            errors.append("index_model_id_or_revision_mismatch")
        if manifest.get("corpus_sha256") != corpus_hash:
            errors.append("index_corpus_hash_mismatch")
        if manifest.get("source_lock_sha256") != lock_hash:
            errors.append("index_source_lock_hash_mismatch")
        if manifest.get("vectors_sha256") != _sha256(vectors_path):
            errors.append("index_vector_file_hash_mismatch")
        if manifest.get("chunk_ids") != row_ids:
            errors.append("index_chunk_order_mismatch")
        if manifest.get("count") != len(rows):
            errors.append("index_chunk_count_mismatch")
        if not isinstance(manifest.get("dimension"), int) or manifest["dimension"] <= 0:
            errors.append("index_dimension_invalid")

        model_path = model_dir / "model.safetensors"
        if not model_path.is_file():
            errors.append("embedding_model_weights_missing")
        else:
            model_hash = _sha256(model_path)
            if manifest.get("model_sha256") != model_hash:
                errors.append("embedding_model_weights_hash_mismatch")
            suffixes = {".json", ".txt", ".model", ".safetensors", ".bin"}
            assets = {path.relative_to(model_dir).as_posix(): _sha256(path)
                      for path in sorted(model_dir.rglob("*"))
                      if path.is_file() and path.suffix in suffixes}
            if manifest.get("model_assets_sha256") != assets:
                errors.append("embedding_model_assets_mismatch")
        try:
            vectors = np.load(vectors_path, allow_pickle=False)
            vector_shape = list(vectors.shape)
            if vectors.dtype != np.float32 or vectors.shape != (len(rows), manifest.get("dimension")):
                errors.append("index_vector_shape_or_dtype_mismatch")
            elif not np.all(np.isfinite(vectors)) or not np.allclose(np.linalg.norm(vectors, axis=1), 1, atol=1e-4):
                errors.append("index_vectors_not_finite_and_normalized")
        except (OSError, ValueError) as exc:
            errors.append(f"index_vectors_unreadable:{type(exc).__name__}")

    report_manifest_hash = None
    evaluation_reports_checked = []
    evaluation_comparison_checked = False
    if report_dir is not None:
        report_dir = Path(report_dir).resolve()
        report_manifest_path = report_dir / "manifest.json"
        if not report_manifest_path.is_file():
            errors.append("evaluation_report_manifest_missing")
        else:
            report_manifest_hash = _sha256(report_manifest_path)
            try:
                report_manifest = _read_json(report_manifest_path)
            except (OSError, json.JSONDecodeError) as exc:
                report_manifest = {}
                errors.append(f"evaluation_report_manifest_unreadable:{type(exc).__name__}")
            if report_manifest:
                if report_manifest.get("schema_version") not in {1, 2}:
                    errors.append("unsupported_evaluation_report_manifest_schema")
                expected_manifest_values = {
                    "corpus_sha256": corpus_hash,
                    "source_lock_sha256": lock_hash,
                    "retrieval_config_sha256": retrieval_config_hash,
                    "evidence_config_sha256": _sha256(data_dir / "evidence_config.json"),
                    "index_manifest_sha256": _sha256(index_dir / "manifest.json"),
                    "evaluate_sha256": _sha256(ROOT / "evaluate.py"),
                    "policy_sha256": _sha256(ROOT / "policy.py"),
                }
                for key, expected in expected_manifest_values.items():
                    if key in report_manifest and report_manifest.get(key) != expected:
                        errors.append(f"evaluation_report_manifest_{key}_mismatch")
                    elif key not in report_manifest and report_manifest.get("schema_version") == 2:
                        errors.append(f"evaluation_report_manifest_{key}_missing")
                report_entries = report_manifest.get("reports", [])
                if not isinstance(report_entries, list):
                    errors.append("evaluation_report_manifest_reports_invalid")
                    report_entries = []
                if report_manifest.get("report_count") != len(report_entries):
                    errors.append("evaluation_report_manifest_count_mismatch")
                report_paths = [entry.get("path") for entry in report_entries if isinstance(entry, dict)]
                if len(report_paths) != len(set(report_paths)):
                    errors.append("duplicate_evaluation_report_paths")
                for entry in report_entries:
                    if not isinstance(entry, dict) or not isinstance(entry.get("path"), str):
                        errors.append("evaluation_report_manifest_entry_invalid")
                        continue
                    relative_path = Path(entry["path"])
                    if relative_path.is_absolute() or ".." in relative_path.parts:
                        errors.append(f"evaluation_report_path_unsafe:{entry['path']}")
                        continue
                    report_path = (report_dir / relative_path).resolve()
                    if not report_path.is_relative_to(report_dir):
                        errors.append(f"evaluation_report_path_unsafe:{entry['path']}")
                        continue
                    if not report_path.is_file():
                        errors.append(f"evaluation_report_missing:{entry['path']}")
                        continue
                    if not isinstance(entry.get("sha256"), str) or not re.fullmatch(
                            r"[0-9a-f]{64}", entry["sha256"]):
                        errors.append(f"evaluation_report_hash_invalid:{entry['path']}")
                    elif _sha256(report_path) != entry["sha256"]:
                        errors.append(f"evaluation_report_hash_mismatch:{entry['path']}")
                    if not isinstance(entry.get("dataset_sha256"), str) or not re.fullmatch(
                            r"[0-9a-f]{64}", entry["dataset_sha256"]):
                        errors.append(f"evaluation_report_dataset_hash_invalid:{entry['path']}")
                    elif entry["dataset_sha256"] not in evaluation_dataset_hashes:
                        errors.append(f"evaluation_report_dataset_not_audited:{entry['path']}")
                    for key, expected in expected_manifest_values.items():
                        entry_key = "config_sha256" if key == "retrieval_config_sha256" else key
                        if entry_key == "evidence_config_sha256" and not (
                                entry.get("verify_evidence") or entry.get("rerank_concepts")):
                            continue
                        if entry_key in entry and entry.get(entry_key) != expected:
                            errors.append(f"evaluation_report_manifest_metadata_mismatch:{entry['path']}:{entry_key}")
                        elif entry_key not in entry and report_manifest.get("schema_version") == 2:
                            errors.append(f"evaluation_report_manifest_metadata_missing:{entry['path']}:{entry_key}")
                    try:
                        report = _read_json(report_path)
                    except (OSError, json.JSONDecodeError) as exc:
                        errors.append(f"evaluation_report_unreadable:{entry['path']}:{type(exc).__name__}")
                        continue
                    questions = report.get("questions") if isinstance(report, dict) else None
                    if not isinstance(questions, list) or not questions:
                        errors.append(f"evaluation_report_questions_invalid:{entry['path']}")
                        continue
                    report_fields = ("corpus_sha256", "source_lock_sha256", "dataset_sha256",
                                     "config_sha256", "index_manifest_sha256", "mode",
                                     "apply_policy", "verify_evidence", "rerank_concepts", "split")
                    for field in report_fields:
                        if field in entry and report.get(field) != entry[field]:
                            errors.append(f"evaluation_report_metadata_mismatch:{entry['path']}:{field}")
                    if (entry.get("verify_evidence") or entry.get("rerank_concepts")) and (
                            report.get("evidence_config_sha256") != entry.get("evidence_config_sha256")):
                        errors.append(f"evaluation_report_metadata_mismatch:{entry['path']}:evidence_config_sha256")
                    if "question_count" in entry and len(questions) != entry["question_count"]:
                        errors.append(f"evaluation_report_question_count_mismatch:{entry['path']}")
                    dataset_questions = evaluation_dataset_by_hash.get(entry.get("dataset_sha256"))
                    if dataset_questions is not None:
                        selected_questions = [question for question in dataset_questions
                                              if entry.get("split") == "all"
                                              or question.get("split") == entry.get("split")]
                        expected_ids = [question.get("id") for question in selected_questions]
                        actual_ids = [question.get("id") if isinstance(question, dict) else None
                                      for question in questions]
                        if actual_ids != expected_ids:
                            errors.append(f"evaluation_report_question_ids_mismatch:{entry['path']}")
                        else:
                            for source_question, result_question in zip(selected_questions, questions):
                                source_groups = source_question.get("evidence_groups") or (
                                    [source_question["evidence"]] if source_question.get("evidence") else [])
                                expected_answerable = bool(source_groups or source_question.get("source_id"))
                                expected_status = source_question.get(
                                    "expected_status", "candidates_found" if expected_answerable else
                                    source_question.get("expected_behavior", "insufficient_evidence"))
                                if (result_question.get("split") != source_question.get("split", "regression")
                                        or result_question.get("answerable") != expected_answerable
                                        or result_question.get("expected_status") != expected_status):
                                    errors.append(f"evaluation_report_question_labels_mismatch:{entry['path']}:{source_question.get('id')}")
                    if "metrics" in entry and any(report.get(key) != value
                                                   for key, value in entry["metrics"].items()):
                        errors.append(f"evaluation_report_metrics_mismatch:{entry['path']}")
                    for result_question in questions:
                        retrieved = result_question.get("retrieved")
                        if (not isinstance(retrieved, list)
                                or result_question.get("hits") != len(retrieved)
                                or len(retrieved) > report.get("top_k", 0)):
                            errors.append(f"evaluation_report_hits_invalid:{entry['path']}:{result_question.get('id')}")
                            continue
                        hit_ids = [hit.get("chunk_id") for hit in retrieved if isinstance(hit, dict)]
                        if len(hit_ids) != len(retrieved) or len(hit_ids) != len(set(hit_ids)):
                            errors.append(f"evaluation_report_hit_ids_invalid:{entry['path']}:{result_question.get('id')}")
                        for hit in retrieved:
                            if not isinstance(hit, dict):
                                continue
                            corpus_row = row_by_id.get(hit.get("chunk_id"))
                            if (corpus_row is None or any(hit.get(key) != corpus_row.get(key)
                                                          for key in ("source_id", "section", "text_sha256", "url"))):
                                errors.append(f"evaluation_report_hit_provenance_mismatch:{entry['path']}:{result_question.get('id')}:{hit.get('chunk_id')}")
                            if any(not isinstance(hit.get(key), (int, float))
                                   or not math.isfinite(hit[key]) for key in ("score", "ranking_score")):
                                errors.append(f"evaluation_report_hit_score_invalid:{entry['path']}:{result_question.get('id')}:{hit.get('chunk_id')}")
                    evaluation_reports_checked.append(entry["path"])
                comparison = report_manifest.get("comparison")
                if comparison is not None:
                    if not isinstance(comparison, dict) or not isinstance(comparison.get("path"), str):
                        errors.append("evaluation_comparison_manifest_entry_invalid")
                    else:
                        comparison_relative = Path(comparison["path"])
                        if comparison_relative.is_absolute() or ".." in comparison_relative.parts:
                            errors.append("evaluation_comparison_path_unsafe")
                        else:
                            comparison_path = (report_dir / comparison_relative).resolve()
                            if not comparison_path.is_relative_to(report_dir):
                                errors.append("evaluation_comparison_path_unsafe")
                            elif not comparison_path.is_file():
                                errors.append("evaluation_comparison_missing")
                            elif (not isinstance(comparison.get("sha256"), str)
                                  or not re.fullmatch(r"[0-9a-f]{64}", comparison["sha256"])):
                                errors.append("evaluation_comparison_hash_invalid")
                            elif _sha256(comparison_path) != comparison["sha256"]:
                                errors.append("evaluation_comparison_hash_mismatch")
                            else:
                                try:
                                    comparison_data = _read_json(comparison_path)
                                except (OSError, json.JSONDecodeError) as exc:
                                    comparison_data = {}
                                    errors.append(f"evaluation_comparison_unreadable:{type(exc).__name__}")
                                if (not isinstance(comparison_data.get("reports"), list)
                                        or comparison.get("reports_compared") != len(comparison_data["reports"])):
                                    errors.append("evaluation_comparison_report_count_mismatch")
                                else:
                                    comparison_rows = comparison_data["reports"]
                                    expected_paths = [entry.get("path") for entry in report_entries
                                                      if isinstance(entry, dict)]
                                    actual_paths = [row.get("report") if isinstance(row, dict) else None
                                                    for row in comparison_rows]
                                    if actual_paths != expected_paths:
                                        errors.append("evaluation_comparison_report_paths_mismatch")
                                    if comparison_data.get("schema_version") != 1:
                                        errors.append("evaluation_comparison_schema_unsupported")
                                    if comparison_data.get("current_snapshot") != report_dir.name:
                                        errors.append("evaluation_comparison_current_snapshot_mismatch")
                                    report_by_path = {
                                        entry.get("path"): entry for entry in report_entries
                                        if isinstance(entry, dict) and isinstance(entry.get("path"), str)
                                    }
                                    for row in comparison_rows:
                                        if not isinstance(row, dict) or not isinstance(row.get("report"), str):
                                            errors.append("evaluation_comparison_entry_invalid")
                                            continue
                                        current_entry = report_by_path.get(row["report"])
                                        changed_metrics = row.get("changed_metrics")
                                        if not isinstance(changed_metrics, dict):
                                            errors.append(f"evaluation_comparison_metrics_invalid:{row['report']}")
                                            continue
                                        if current_entry is None:
                                            continue
                                        for field in ("dataset_sha256_previous", "dataset_sha256_current"):
                                            value = row.get(field)
                                            if not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{64}", value):
                                                errors.append(f"evaluation_comparison_dataset_hash_invalid:{row['report']}:{field}")
                                        for field in ("question_count_previous", "question_count_current"):
                                            value = row.get(field)
                                            if type(value) is not int or value < 0:
                                                errors.append(f"evaluation_comparison_question_count_invalid:{row['report']}:{field}")
                                        if (row.get("dataset_sha256_current") != current_entry.get("dataset_sha256")
                                                or row.get("question_count_current") != current_entry.get("question_count")):
                                            errors.append(f"evaluation_comparison_current_metadata_mismatch:{row['report']}")
                                        current_metrics = current_entry.get("metrics", {})
                                        if not isinstance(current_metrics, dict):
                                            errors.append(f"evaluation_comparison_manifest_metrics_invalid:{row['report']}")
                                            continue
                                        for metric, delta in changed_metrics.items():
                                            if (not isinstance(delta, dict) or "previous" not in delta
                                                    or "current" not in delta
                                                    or delta.get("previous") == delta.get("current")
                                                    or metric not in current_metrics
                                                    or delta.get("current") != current_metrics.get(metric)):
                                                errors.append(f"evaluation_comparison_metric_mismatch:{row['report']}:{metric}")
                                    if not any(error.startswith("evaluation_comparison_")
                                               for error in errors):
                                        evaluation_comparison_checked = True

    return {
        "status": "PASS" if not errors else "FAIL",
        "scope": "artifact_integrity_and_provenance_only_not_medical_validity",
        "audit_implementation_sha256": _sha256(Path(__file__)),
        "source_count": len(sources), "chunk_count": len(rows),
        "evaluation_sets_checked": evidence_sets, "vector_shape": vector_shape,
        "evaluation_reports_checked": evaluation_reports_checked,
        "evaluation_comparison_checked": evaluation_comparison_checked,
        "evaluation_dataset_hashes_checked_count": len(evaluation_dataset_hashes),
        "evaluation_report_manifest_sha256": report_manifest_hash,
        "source_cache_checked": source_cache_checked,
        "source_cache_missing": source_cache_missing,
        "model_id": MODEL_ID, "model_revision": MODEL_REVISION, "model_sha256": model_hash,
        "corpus_sha256": corpus_hash, "source_lock_sha256": lock_hash,
        "index_manifest_sha256": manifest_hash,
        "retrieval_config_sha256": retrieval_config_hash, "errors": errors,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=DATA)
    parser.add_argument("--index-dir", type=Path, default=INDEX)
    parser.add_argument("--model-dir", type=Path, default=DEFAULT_MODEL_DIR)
    parser.add_argument("--cache-dir", type=Path, default=DEFAULT_CACHE)
    parser.add_argument("--report-dir", type=Path, default=DEFAULT_REPORT_DIR,
                        help="directory containing a report manifest.json and evaluation reports")
    parser.add_argument("--output", type=Path, help="optional path for the JSON audit report")
    args = parser.parse_args()
    report = audit(args.data_dir, args.index_dir, args.model_dir, args.cache_dir, args.report_dir)
    serialized = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(serialized, encoding="utf-8")
    print(serialized, end="")
    if report["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
