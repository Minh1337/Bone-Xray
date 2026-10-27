"""Local, version-checked semantic retrieval over the public NCI corpus."""

import hashlib
import json
import argparse
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
INDEX = ROOT / "index"
MODEL = ROOT / "models" / "e5-small"
MODEL_ID = "intfloat/multilingual-e5-small"
MODEL_REVISION = "8d923955b027282ba975c0a4c825486c9ca4c490"
CORPUS = DATA / "corpus.jsonl"
LOCK = DATA / "source_lock.json"


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rows():
    result = [json.loads(line) for line in CORPUS.read_text(encoding="utf-8").splitlines() if line]
    if not result or len({row["chunk_id"] for row in result}) != len(result):
        raise ValueError("Corpus empty or duplicate chunk IDs")
    for row in result:
        if hashlib.sha256(row["text"].encode("utf-8")).hexdigest() != row["text_sha256"]:
            raise ValueError(f"Changed chunk text: {row['chunk_id']}")
    return result


def load_model():
    if not (MODEL / "modules.json").is_file():
        raise FileNotFoundError("Embedding model missing; run rag/build_index.py --download-model")
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer(str(MODEL), device="cpu", local_files_only=True)


def load_index():
    manifest = json.loads((INDEX / "manifest.json").read_text(encoding="utf-8"))
    corpus_rows = rows()
    if manifest["corpus_sha256"] != sha256(CORPUS) or manifest["source_lock_sha256"] != sha256(LOCK):
        raise ValueError("Index stale: corpus or source lock changed; rebuild it")
    if manifest["model_id"] != MODEL_ID or manifest["model_revision"] != MODEL_REVISION:
        raise ValueError("Index model mismatch")
    if manifest["model_sha256"] != sha256(MODEL / "model.safetensors"):
        raise ValueError("Embedding model changed; rebuild index")
    if manifest["chunk_ids"] != [row["chunk_id"] for row in corpus_rows]:
        raise ValueError("Index chunk order mismatch")
    if manifest["vectors_sha256"] != sha256(INDEX / "vectors.npy"):
        raise ValueError("Index vectors changed")
    vectors = np.load(INDEX / "vectors.npy", allow_pickle=False)
    if vectors.shape != (len(corpus_rows), manifest["dimension"]) or vectors.dtype != np.float32:
        raise ValueError("Index vector shape/dtype mismatch")
    return corpus_rows, vectors


def search(question, *, top_k=5, min_score=None, source_ids=None, model=None, index=None):
    if not question.strip() or top_k < 1:
        raise ValueError("Question must be nonempty and top_k positive")
    corpus_rows, vectors = index if index is not None else load_index()
    model = model or load_model()
    query = model.encode(["query: " + question.strip()], normalize_embeddings=True)[0]
    query = np.asarray(query, dtype=np.float32)
    if query.shape != (vectors.shape[1],):
        raise ValueError("Query vector dimension mismatch")
    scores = vectors @ query
    allowed = set(source_ids) if source_ids else None
    order = sorted(range(len(scores)), key=lambda i: (-float(scores[i]), corpus_rows[i]["chunk_id"]))
    result = []
    for i in order:
        row = corpus_rows[i]
        if allowed is not None and row["source_id"] not in allowed:
            continue
        score = float(scores[i])
        if min_score is not None and score < min_score:
            continue
        result.append({**row, "score": score})
        if len(result) == top_k:
            break
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Search the local NCI corpus")
    parser.add_argument("question")
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--min-score", type=float)
    parser.add_argument("--source-id", action="append")
    args = parser.parse_args()
    hits = search(args.question, top_k=args.top_k, min_score=args.min_score,
                  source_ids=args.source_id)
    print(json.dumps(hits, ensure_ascii=False, indent=2))
