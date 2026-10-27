import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np

from rag import retrieval as r


class FakeModel:
    def encode(self, values, **kwargs):
        assert values[0].startswith("query: ")
        return np.array([[1.0, 0.0]], dtype=np.float32)


class RetrievalTests(unittest.TestCase):
    def test_search_keeps_citations_filters_and_threshold(self):
        rows = [{"chunk_id": "a", "source_id": "s1", "section": "A", "url": "https://example.org/a", "text": "a"},
                {"chunk_id": "b", "source_id": "s2", "section": "B", "url": "https://example.org/b", "text": "b"}]
        vectors = np.array([[1, 0], [0, 1]], dtype=np.float32)
        hits = r.search("câu hỏi", index=(rows, vectors), model=FakeModel(), source_ids=["s1"], min_score=0.5)
        self.assertEqual([(h["chunk_id"], h["url"]) for h in hits], [("a", "https://example.org/a")])
        self.assertEqual(r.search("câu hỏi", index=(rows, vectors), model=FakeModel(), min_score=1.1), [])

    def test_index_rejects_changed_source_lock(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            corpus, lock = base / "corpus.jsonl", base / "source_lock.json"
            index, model = base / "index", base / "model"
            index.mkdir()
            model.mkdir()
            corpus.write_text(json.dumps({"chunk_id": "a", "text": "x", "text_sha256":
                                          hashlib.sha256(b"x").hexdigest()}) + "\n")
            lock.write_text("original")
            (model / "model.safetensors").write_bytes(b"model")
            np.save(index / "vectors.npy", np.zeros((1, 2), dtype=np.float32))
            manifest = {"corpus_sha256": r.sha256(corpus), "source_lock_sha256": r.sha256(lock),
                        "model_id": r.MODEL_ID, "model_revision": r.MODEL_REVISION,
                        "model_sha256": r.sha256(model / "model.safetensors"),
                        "vectors_sha256": r.sha256(index / "vectors.npy"),
                        "chunk_ids": ["a"], "dimension": 2}
            (index / "manifest.json").write_text(json.dumps(manifest))
            lock.write_text("changed")
            with patch.multiple(r, CORPUS=corpus, LOCK=lock, INDEX=index, MODEL=model):
                with self.assertRaisesRegex(ValueError, "stale"):
                    r.load_index()


if __name__ == "__main__":
    unittest.main()
