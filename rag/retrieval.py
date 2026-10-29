"""Local, version-checked semantic retrieval over the public NCI corpus."""

import hashlib
import json
import argparse
from pathlib import Path

import numpy as np

try:
    from rag.lexical import BM25, contains, expansion, fuse
    from rag.policy import assess
    from rag.evidence import EvidenceVerifier
except ModuleNotFoundError:
    from lexical import BM25, contains, expansion, fuse
    from policy import assess
    from evidence import EvidenceVerifier


ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
INDEX = ROOT / "index"
MODEL = ROOT / "models" / "e5-small"
MODEL_ID = "intfloat/multilingual-e5-small"
MODEL_REVISION = "8d923955b027282ba975c0a4c825486c9ca4c490"
CORPUS = DATA / "corpus.jsonl"
LOCK = DATA / "source_lock.json"
CONFIG = DATA / "retrieval_config.json"


def load_config():
    return json.loads(CONFIG.read_text(encoding="utf-8"))


def model_asset_hashes():
    """Tokenization, pooling and model settings affect embeddings as well as weights."""
    suffixes = {'.json', '.txt', '.model', '.safetensors', '.bin'}
    return {path.relative_to(MODEL).as_posix(): sha256(path) for path in sorted(MODEL.rglob('*'))
            if path.is_file() and path.suffix in suffixes}


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
    if manifest.get('schema_version') != 2:
        raise ValueError('Index schema changed; run rag/build_index.py to rebuild')
    if (manifest.get('embedding_input') != 'passage: {section}\n{text}'
            or manifest.get('normalized') is not True):
        raise ValueError('Index embedding input or normalization contract mismatch; rebuild index')
    corpus_rows = rows()
    if manifest.get('count') != len(corpus_rows):
        raise ValueError('Index chunk count mismatch; rebuild index')
    if manifest["corpus_sha256"] != sha256(CORPUS) or manifest["source_lock_sha256"] != sha256(LOCK):
        raise ValueError("Index stale: corpus or source lock changed; rebuild it")
    if manifest["model_id"] != MODEL_ID or manifest["model_revision"] != MODEL_REVISION:
        raise ValueError("Index model mismatch")
    if manifest["model_sha256"] != sha256(MODEL / "model.safetensors"):
        raise ValueError("Embedding model changed; rebuild index")
    if manifest['model_assets_sha256'] != model_asset_hashes():
        raise ValueError('Embedding tokenizer/configuration changed; rebuild index')
    if manifest["chunk_ids"] != [row["chunk_id"] for row in corpus_rows]:
        raise ValueError("Index chunk order mismatch")
    if manifest["vectors_sha256"] != sha256(INDEX / "vectors.npy"):
        raise ValueError("Index vectors changed")
    vectors = np.load(INDEX / "vectors.npy", allow_pickle=False)
    if vectors.shape != (len(corpus_rows), manifest["dimension"]) or vectors.dtype != np.float32:
        raise ValueError("Index vector shape/dtype mismatch")
    if not np.all(np.isfinite(vectors)) or not np.allclose(np.linalg.norm(vectors, axis=1), 1, atol=1e-4):
        raise ValueError('Index vectors must be finite and L2 normalized')
    return corpus_rows, vectors


class Retriever:
    def __init__(self, *, model=None, index=None, config=None):
        self.corpus_rows, self.vectors = index if index is not None else load_index()
        self.model = model
        self.config = config if config is not None else load_config()
        self.lexical = None
        self.verifier = None
    def search(self, question, *, top_k=5, min_score=None, source_ids=None, mode="hybrid"):
        if not question.strip() or top_k < 1 or mode not in {"dense", "hybrid"}:
            raise ValueError("Question must be nonempty, top_k positive, mode dense or hybrid")
        if min_score is not None and not np.isfinite(min_score):
            raise ValueError("min_score must be finite")
        expanded = expansion(question, self.config) if mode == "hybrid" else ""
        queries = ["query: " + question.strip()]
        if expanded:
            queries.append("query: " + expanded)
        if self.model is None:
            self.model = load_model()
        encoded = np.asarray(self.model.encode(queries, normalize_embeddings=True), dtype=np.float32)
        if encoded.shape != (len(queries), self.vectors.shape[1]) or not np.all(np.isfinite(encoded)):
            raise ValueError("Query vector dimension or values invalid")
        similarities = self.vectors @ encoded.T
        scores = similarities[:, 0]
        allowed = set(source_ids) if source_ids is not None else None
        candidates = [i for i, row in enumerate(self.corpus_rows)
                      if (allowed is None or row['source_id'] in allowed)
                      and (min_score is None or scores[i] >= min_score)]

        def ordered(values, indices):
            return sorted(indices, key=lambda i: (-float(values[i]), self.corpus_rows[i]['chunk_id']))

        order = ordered(scores, candidates)
        ranking_scores = scores
        if mode == "hybrid":
            limit = self.config['candidate_limit']
            rankings = [ordered(similarities[:, j], candidates)[:limit] for j in range(len(queries))]
            if self.lexical is None:
                self.lexical = BM25(self.corpus_rows, self.config)
            keyword_scores = self.lexical.score(question + ' ' + expanded)
            rankings.append(ordered(keyword_scores, [i for i in candidates if keyword_scores[i] > 0])[:limit])
            weights = self.config['rrf_weights']
            rank_weights = [weights['original_dense']]
            if expanded:
                rank_weights.append(weights['expanded_dense'])
            rank_weights.append(weights['lexical'])
            ranking_scores = fuse(rankings, len(scores), self.config['rrf_constant'], rank_weights)
            order = ordered(ranking_scores, [i for i in candidates if ranking_scores[i] > 0])
        return [{**self.corpus_rows[i], 'score': float(scores[i]),
                 'ranking_score': float(ranking_scores[i]), 'retrieval_mode': mode}
                for i in order[:top_k]]


def resolve_source_route(question, config):
    """Return a source preference only for explicit, high-precision topic cues."""
    matches = []
    for route in config.get('source_routes', []):
        if any(contains(question, cue) for cue in route.get('terms', [])):
            matches.append(route['source_id'])
    # Ambiguous questions retain corpus-wide retrieval instead of intersecting
    # unrelated source scopes or silently choosing one.
    return matches[0] if len(matches) == 1 else None


def requests_source_overview(question, config):
    return any(contains(question, cue) for cue in config.get('overview_cues', []))


def _route_candidates(engine, question, *, top_k, min_score, source_ids, mode, route_source_id):
    """Reserve one result from an explicit source cue, then fill globally."""
    # Respect caller restrictions; a route cannot widen an explicit allowlist.
    if source_ids is not None and route_source_id not in source_ids:
        return engine.search(question, top_k=top_k, min_score=min_score,
                             source_ids=source_ids, mode=mode)
    preferred = engine.search(question, top_k=top_k, min_score=min_score,
                              source_ids=[route_source_id], mode=mode)
    broad = engine.search(question, top_k=top_k, min_score=min_score,
                          source_ids=source_ids, mode=mode)
    # Keep a small source-specific slice so a closely matched section is not
    # lost to cross-source noise. A route can request a slightly larger slice
    # when its topic-specific source has several short, complementary chunks.
    preferred_count = next((route.get('preferred_count', 2)
                            for route in engine.config.get('source_routes', [])
                            if route.get('source_id') == route_source_id), 2)
    if not isinstance(preferred_count, int) or preferred_count < 1:
        raise ValueError(f'Invalid preferred_count for source route: {route_source_id}')
    chosen = preferred[:min(preferred_count, top_k)]
    chosen_ids = {hit['chunk_id'] for hit in chosen}
    chosen.extend(hit for hit in broad if hit['chunk_id'] not in chosen_ids)
    return chosen[:top_k]


def _overview_candidates(engine, question, *, top_k, min_score, source_ids, mode, route_source_id):
    """For explicit overview requests, surface that source's abstract if present."""
    if source_ids is not None and route_source_id not in source_ids:
        return engine.search(question, top_k=top_k, min_score=min_score,
                             source_ids=source_ids, mode=mode)
    source_pool = engine.search(question, top_k=max(top_k, engine.config['candidate_limit']),
                                min_score=min_score, source_ids=[route_source_id], mode=mode)
    abstract = next((hit for hit in source_pool if hit.get('section', '').strip().casefold() == 'abstract'), None)
    broad = engine.search(question, top_k=top_k, min_score=min_score,
                          source_ids=source_ids, mode=mode)
    chosen = [abstract] if abstract else []
    chosen_ids = {hit['chunk_id'] for hit in chosen}
    chosen.extend(hit for hit in source_pool if hit['chunk_id'] not in chosen_ids)
    chosen_ids = {hit['chunk_id'] for hit in chosen}
    chosen.extend(hit for hit in broad if hit['chunk_id'] not in chosen_ids)
    return chosen[:top_k]


def search(question, *, top_k=5, min_score=None, source_ids=None, model=None, index=None, mode="dense"):
    """Raw search retained for comparisons; it does not enforce scope or safety."""
    return Retriever(model=model, index=index).search(question, top_k=top_k, min_score=min_score,
                                                     source_ids=source_ids, mode=mode)


def retrieve(question, *, engine=None, top_k=5, min_score=None, source_ids=None, mode="hybrid",
             verify_evidence=False, rerank_concepts=False):
    """Route unsupported requests before loading the model; return candidate evidence only."""
    if verify_evidence and rerank_concepts:
        raise ValueError('Select strict evidence filtering or concept reranking, not both')
    config = engine.config if engine is not None else load_config()
    status, reason = assess(question, config)
    hits = []
    diagnostics = None
    route_source_id = None
    prefer_abstract = False
    if status is None:
        engine = engine if engine is not None else Retriever(config=config)
        route_source_id = resolve_source_route(question, config) if source_ids is None else None
        prefer_abstract = bool(route_source_id and requests_source_overview(question, config))
        if verify_evidence or rerank_concepts:
            if engine.verifier is None:
                engine.verifier = EvidenceVerifier(engine.corpus_rows)
            pool = max(top_k, engine.verifier.config['candidate_pool'])
            candidate_route = _overview_candidates if prefer_abstract else _route_candidates
            candidates = (candidate_route(engine, question, top_k=pool, min_score=min_score,
                                          source_ids=source_ids, mode=mode, route_source_id=route_source_id)
                          if route_source_id else
                          engine.search(question, top_k=pool, min_score=min_score, source_ids=source_ids, mode=mode))
            hits, reason, diagnostics = engine.verifier.check(question, candidates, top_k=top_k,
                                                             rerank_only=rerank_concepts)
        else:
            candidate_route = _overview_candidates if prefer_abstract else _route_candidates
            hits = (candidate_route(engine, question, top_k=top_k, min_score=min_score,
                                    source_ids=source_ids, mode=mode, route_source_id=route_source_id)
                    if route_source_id else
                    engine.search(question, top_k=top_k, min_score=min_score, source_ids=source_ids, mode=mode))
            reason = 'unvalidated_candidates' if hits else 'no_hits_above_threshold_or_filter'
        status = 'candidates_found' if hits else 'insufficient_evidence'
    result = {'status': status, 'reason': reason, 'answer_ready': False, 'hits': hits}
    if route_source_id:
        result['preferred_source_id'] = route_source_id
    if prefer_abstract:
        result['preferred_section'] = 'Abstract'
    if verify_evidence or rerank_concepts:
        result['evidence_check'] = diagnostics
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Search the local NCI corpus")
    parser.add_argument("question")
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--min-score", type=float)
    parser.add_argument("--source-id", action="append")
    parser.add_argument("--mode", choices=["dense", "hybrid"], default="hybrid")
    parser.add_argument("--raw", action="store_true", help="bypass query routing for retrieval diagnostics")
    parser.add_argument("--verify-evidence", action="store_true", help="experimental lexical coverage filter/reranker")
    parser.add_argument("--rerank-concepts", action="store_true", help="experimental concept reranking without strict filtering")
    args = parser.parse_args()
    if args.raw and (args.verify_evidence or args.rerank_concepts):
        parser.error('Evidence experiments require routed retrieval; remove --raw')
    if args.verify_evidence and args.rerank_concepts:
        parser.error('Select --verify-evidence or --rerank-concepts')
    operation = search if args.raw else retrieve
    options = {'top_k': args.top_k, 'min_score': args.min_score, 'source_ids': args.source_id, 'mode': args.mode}
    if not args.raw:
        options['verify_evidence'] = args.verify_evidence
        options['rerank_concepts'] = args.rerank_concepts
    result = operation(args.question, **options)
    print(json.dumps(result, ensure_ascii=False, indent=2))
