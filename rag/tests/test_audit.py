import hashlib
import json
import tempfile
import unittest
from pathlib import Path

import numpy as np

from rag.audit import MODEL_ID, MODEL_REVISION, audit


class ArtifactAuditTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.data, self.index = self.root / "data", self.root / "index"
        self.model = self.root / "model"
        self.data.mkdir()
        self.index.mkdir()
        self.model.mkdir()
        self.source = {"id": "source-a", "title": "Source A",
                       "url": "https://openorthopaedicsjournal.com/article",
                       "authors": "Author", "publisher": "Publisher",
                       "license": "CC BY 4.0", "license_url": "https://creativecommons.org/licenses/by/4.0/",
                       "scope": "Limited scope"}
        self.text = "A reproducible evidence paragraph."
        text_hash = hashlib.sha256(self.text.encode()).hexdigest()
        source_hash = hashlib.sha256(b"fixture source payload").hexdigest()
        self.row = {"chunk_id": "source-a:0001", "source_id": "source-a", "title": "Source A",
                    "url": self.source["url"], "authors": "Author", "publisher": "Publisher",
                    "license": "CC BY 4.0", "license_url": "https://creativecommons.org/licenses/by/4.0/",
                    "scope": "Limited scope", "section": "Results", "text": self.text,
                    "text_sha256": text_hash, "source_sha256": source_hash}
        second_text = "A second evidence paragraph without the selected quote."
        self.row2 = {**self.row, "chunk_id": "source-a:0002", "section": "Discussion",
                     "text": second_text, "text_sha256": hashlib.sha256(second_text.encode()).hexdigest()}
        self.lock = [{"id": self.source["id"], **{key: self.row[key] for key in
                      ("title", "url", "authors", "publisher", "license", "license_url", "scope")},
                      "chunk_count": 2, "source_sha256": source_hash}]
        self._write(self.data / "sources.json", [self.source])
        self._write(self.data / "source_lock.json", self.lock)
        (self.data / "corpus.jsonl").write_text(json.dumps(self.row) + "\n" + json.dumps(self.row2) + "\n",
                                                 encoding="utf-8")
        corpus_hash = self._hash(self.data / "corpus.jsonl")
        self._write(self.data / "evaluation_v2.json", {"corpus_sha256": corpus_hash, "questions": [
            {"id": "q1", "evidence_quote": "reproducible evidence", "evidence": [
                {"chunk_id": self.row["chunk_id"], "source_id": "source-a", "section": "Results",
                 "text_sha256": text_hash},
                {"chunk_id": self.row2["chunk_id"], "source_id": "source-a", "section": "Discussion",
                 "text_sha256": self.row2["text_sha256"]}]}]})
        vectors = np.array([[1.0, 0.0], [0.0, 1.0]], dtype=np.float32)
        np.save(self.index / "vectors.npy", vectors)
        (self.model / "model.safetensors").write_bytes(b"pinned test weights")
        (self.model / "config.json").write_text('{"model_type":"test"}', encoding="utf-8")
        model_asset_suffixes = {".json", ".txt", ".model", ".safetensors", ".bin"}
        model_assets = {path.relative_to(self.model).as_posix(): self._hash(path)
                        for path in sorted(self.model.rglob("*"))
                        if path.is_file() and path.suffix in model_asset_suffixes}
        self._write(self.index / "manifest.json", {
            "schema_version": 2, "embedding_input": "passage: {section}\n{text}", "normalized": True,
            "corpus_sha256": corpus_hash,
            "source_lock_sha256": self._hash(self.data / "source_lock.json"),
            "vectors_sha256": self._hash(self.index / "vectors.npy"),
            "chunk_ids": [self.row["chunk_id"], self.row2["chunk_id"]],
            "dimension": 2, "count": 2, "model_id": MODEL_ID, "model_revision": MODEL_REVISION,
            "model_sha256": self._hash(self.model / "model.safetensors"),
            "model_assets_sha256": model_assets,
        })

    def tearDown(self):
        self.temp.cleanup()

    @staticmethod
    def _write(path, value):
        path.write_text(json.dumps(value), encoding="utf-8")

    @staticmethod
    def _hash(path):
        return hashlib.sha256(path.read_bytes()).hexdigest()

    def test_consistent_corpus_gold_and_index_pass(self):
        report = audit(self.data, self.index, self.model)
        self.assertEqual(report["status"], "PASS", report["errors"])
        self.assertEqual(report["vector_shape"], [2, 2])
        self.assertEqual(report["scope"], "artifact_integrity_and_provenance_only_not_medical_validity")

    def test_audit_discovers_new_evaluation_datasets_without_allowlist_edits(self):
        corpus_hash = self._hash(self.data / "corpus.jsonl")
        dataset = {"corpus_sha256": corpus_hash, "questions": [{
            "id": "new", "expected_status": "candidates_found",
            "evidence": [{"chunk_id": self.row["chunk_id"], "source_id": "source-a",
                          "section": "Results", "text_sha256": self.row["text_sha256"]}]}]}
        self._write(self.data / "evaluation_future_probe.json", dataset)
        report = audit(self.data, self.index, self.model)
        self.assertEqual(report["status"], "PASS", report["errors"])
        self.assertIn("evaluation_future_probe.json", report["evaluation_sets_checked"])
        self.assertEqual(report["evaluation_dataset_hashes_checked_count"], 2)

    def test_corpus_drift_and_missing_gold_evidence_are_reported(self):
        self.row["text"] = "Changed text."
        (self.data / "corpus.jsonl").write_text(json.dumps(self.row) + "\n", encoding="utf-8")
        report = audit(self.data, self.index, self.model)
        self.assertEqual(report["status"], "FAIL")
        self.assertIn("chunk_text_hash_mismatch:source-a:0001", report["errors"])
        self.assertIn("index_corpus_hash_mismatch", report["errors"])
        self.assertIn("evaluation_corpus_hash_mismatch:evaluation_v2.json", report["errors"])

    def test_source_outside_ingest_allowlist_fails_audit(self):
        source = {**self.source, "url": "https://unapproved.example/article"}
        self._write(self.data / "sources.json", [source])
        report = audit(self.data, self.index, self.model)
        self.assertEqual(report["status"], "FAIL")
        self.assertTrue(any(error.startswith("source_validation_failed:source-a:") for error in report["errors"]))

    def test_source_metadata_drift_fails_audit(self):
        self._write(self.data / "sources.json", [{**self.source, "authors": "Unverified Author"}])
        report = audit(self.data, self.index, self.model)
        self.assertIn("source_declaration_changed:source-a:authors", report["errors"])

    def test_stale_gold_chunk_id_fails_even_when_text_hash_is_valid(self):
        path = self.data / "evaluation_v2.json"
        dataset = json.loads(path.read_text(encoding="utf-8"))
        dataset["questions"][0]["evidence"][0]["chunk_id"] = "stale-chunk-id"
        self._write(path, dataset)
        report = audit(self.data, self.index, self.model)
        self.assertIn("evaluation_evidence_chunk_id_mismatch:evaluation_v2.json:q1", report["errors"])

    def test_embedding_model_asset_drift_fails_audit(self):
        (self.model / "config.json").write_text('{"model_type":"changed"}', encoding="utf-8")
        report = audit(self.data, self.index, self.model)
        self.assertIn("embedding_model_assets_mismatch", report["errors"])

    def test_index_embedding_contract_mismatch_fails_audit(self):
        path = self.index / "manifest.json"
        manifest = json.loads(path.read_text(encoding="utf-8"))
        manifest["normalized"] = False
        self._write(path, manifest)
        report = audit(self.data, self.index, self.model)
        self.assertIn("index_embedding_contract_mismatch", report["errors"])


if __name__ == "__main__":
    unittest.main()
