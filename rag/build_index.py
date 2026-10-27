"""Build a local E5 embedding index. Only public corpus text is encoded."""

import argparse
import json

import numpy as np

try:
    from rag import retrieval as r
except ModuleNotFoundError:
    import retrieval as r


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--download-model", action="store_true", help="fetch pinned model before indexing")
    args = parser.parse_args()
    if args.download_model:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer(r.MODEL_ID, revision=r.MODEL_REVISION, device="cpu")
        r.MODEL.parent.mkdir(parents=True, exist_ok=True)
        model.save(str(r.MODEL))
    else:
        model = r.load_model()
    if not (r.MODEL / "model.safetensors").is_file():
        raise FileNotFoundError("Pinned model weights missing")
    corpus_rows = r.rows()
    passages = ["passage: " + row["section"] + "\n" + row["text"] for row in corpus_rows]
    vectors = model.encode(passages, batch_size=16, normalize_embeddings=True, show_progress_bar=True)
    vectors = np.asarray(vectors, dtype=np.float32)
    if vectors.shape[0] != len(corpus_rows) or not np.all(np.isfinite(vectors)):
        raise ValueError("Invalid embedding matrix")
    r.INDEX.mkdir(parents=True, exist_ok=True)
    np.save(r.INDEX / "vectors.npy", vectors, allow_pickle=False)
    manifest = {
        "model_id": r.MODEL_ID,
        "model_revision": r.MODEL_REVISION,
        "model_sha256": r.sha256(r.MODEL / "model.safetensors"),
        "corpus_sha256": r.sha256(r.CORPUS),
        "source_lock_sha256": r.sha256(r.LOCK),
        "vectors_sha256": r.sha256(r.INDEX / "vectors.npy"),
        "chunk_ids": [row["chunk_id"] for row in corpus_rows],
        "dimension": int(vectors.shape[1]),
        "count": len(corpus_rows),
    }
    (r.INDEX / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Indexed {manifest['count']} chunks x {manifest['dimension']} dimensions")


if __name__ == "__main__":
    main()
