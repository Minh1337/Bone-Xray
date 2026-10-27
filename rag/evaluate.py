"""Evaluate raw retrieval and query routing separately; persist reproducible results."""

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

try:
    from rag import retrieval as r
except ModuleNotFoundError:
    import retrieval as r


def evaluate(questions, engine, *, top_k=5, min_score=None, mode='dense', apply_policy=False,
             verify_evidence=False, rerank_concepts=False):
    if (verify_evidence or rerank_concepts) and not apply_policy:
        raise ValueError('Evidence checking requires apply_policy=True')
    results = []
    available = {(row['source_id'], row['section'], row['text_sha256']) for row in engine.corpus_rows}
    for q in questions:
        targets = q.get('evidence', [])
        if any((x['source_id'], x['section'], x['text_sha256']) not in available for x in targets):
            raise ValueError(f"Gold evidence missing or changed: {q['id']}")
        if apply_policy:
            response = r.retrieve(q['question_vi'], engine=engine, top_k=top_k,
                                  min_score=min_score, mode=mode, verify_evidence=verify_evidence,
                                  rerank_concepts=rerank_concepts)
            hits = response['hits']
            status, reason = response['status'], response['reason']
        else:
            hits = engine.search(q['question_vi'], top_k=top_k, min_score=min_score, mode=mode)
            status, reason = ('candidates_found' if hits else 'insufficient_evidence'), 'raw_retrieval'
        answerable = bool(targets or q.get('source_id'))
        if targets:
            wanted = {(x['source_id'], x['section'], x['text_sha256']) for x in targets}
            rank = next((i + 1 for i, h in enumerate(hits)
                         if (h['source_id'], h['section'], h['text_sha256']) in wanted), None)
        elif q.get('source_id'):
            rank = next((i + 1 for i, h in enumerate(hits)
                         if h['source_id'] == q['source_id'] and h['section'] == q['section']), None)
        else:
            rank = None
        expected_status = q.get('expected_status', 'candidates_found' if answerable else
                                q.get('expected_behavior', 'insufficient_evidence'))
        results.append({'id': q['id'], 'split': q.get('split', 'regression'),
                        'answerable': answerable, 'rank': rank, 'expected_status': expected_status,
                        'status': status, 'reason': reason, 'status_match': status == expected_status,
                        'hits': len(hits), 'evidence_check': response.get('evidence_check') if apply_policy else None,
                        'retrieved': [
                            {key: h[key] for key in ('chunk_id', 'source_id', 'section', 'text_sha256',
                                                    'url', 'score', 'ranking_score', 'retrieval_mode')}
                            for h in hits]})
    positive = [x for x in results if x['answerable']]
    negative = [x for x in results if not x['answerable']]
    return {
        'answerable_count': len(positive), 'negative_count': len(negative),
        'recall_at_k': sum(x['rank'] is not None for x in positive) / len(positive) if positive else None,
        'mrr_at_k': sum(1 / x['rank'] for x in positive if x['rank']) / len(positive) if positive else None,
        'negative_abstention': sum(x['hits'] == 0 for x in negative) / len(negative) if negative else None,
        'positive_abstention': sum(x['hits'] == 0 for x in positive) / len(positive) if positive else None,
        'routing_accuracy': sum(x['status_match'] for x in results) / len(results) if results else None,
        'questions': results,
    }


def run_evaluation(dataset_path, *, engine=None, split='all', top_k=5, min_score=None,
                   mode='dense', apply_policy=False, verify_evidence=False, rerank_concepts=False, output=None):
    dataset_path = Path(dataset_path)
    dataset = json.loads(dataset_path.read_text(encoding='utf-8'))
    if isinstance(dataset, dict):
        if dataset['corpus_sha256'] != r.sha256(r.CORPUS):
            raise ValueError('Evaluation corpus changed; review and re-label evidence before running')
        questions = dataset['questions']
    else:
        questions = dataset
    questions = [q for q in questions if split == 'all' or q.get('split') == split]
    if not questions:
        raise ValueError('No questions in requested split')
    engine = engine if engine is not None else r.Retriever()
    report = evaluate(questions, engine, top_k=top_k, min_score=min_score,
                      mode=mode, apply_policy=apply_policy, verify_evidence=verify_evidence,
                      rerank_concepts=rerank_concepts)
    code_paths = ['retrieval.py', 'lexical.py', 'policy.py', 'evidence.py', 'evaluate.py', 'build_corpus.py', 'build_index.py']
    report.update({
        'created_at': datetime.now(timezone.utc).isoformat(),
        'corpus_sha256': r.sha256(r.CORPUS), 'source_lock_sha256': r.sha256(r.LOCK),
        'dataset_sha256': r.sha256(dataset_path), 'config_sha256': r.sha256(r.CONFIG),
        'implementation_sha256': {name: r.sha256(r.ROOT / name) for name in code_paths},
        'model_revision': r.MODEL_REVISION,
        'index_manifest_sha256': r.sha256(r.INDEX / 'manifest.json'),
        'mode': mode, 'apply_policy': apply_policy, 'split': split,
        'verify_evidence': verify_evidence,
        'rerank_concepts': rerank_concepts,
        'top_k': top_k, 'min_score': min_score,
        'gold_type': 'source_section_text_hash' if any(q.get('evidence') for q in questions) else 'source_section',
        'dataset_provenance': dataset.get('provenance') if isinstance(dataset, dict) else 'legacy regression set',
    })
    if isinstance(dataset, dict):
        report['frozen_config_matches'] = dataset.get('config_sha256_at_freeze') == r.sha256(r.CONFIG)
    if verify_evidence or rerank_concepts:
        evidence_hash = r.sha256(r.DATA / 'evidence_config.json')
        report['evidence_config_sha256'] = evidence_hash
        report['frozen_evidence_config_matches'] = (dataset.get('evidence_config_sha256_at_freeze') == evidence_hash
                                                  if isinstance(dataset, dict) else None)
    serialized = json.dumps(report, ensure_ascii=False, indent=2) + '\n'
    if output:
        output = Path(output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(serialized, encoding='utf-8')
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--top-k', type=int, default=5)
    parser.add_argument('--min-score', type=float)
    parser.add_argument('--mode', choices=['dense', 'hybrid'], default='dense')
    parser.add_argument('--apply-policy', action='store_true')
    parser.add_argument('--verify-evidence', action='store_true')
    parser.add_argument('--rerank-concepts', action='store_true')
    parser.add_argument('--dataset', type=Path, default=r.DATA / 'evaluation_questions.json')
    parser.add_argument('--split', choices=['all', 'dev', 'test'], default='all')
    parser.add_argument('--output', type=Path)
    parser.add_argument('--summary', action='store_true')
    args = parser.parse_args()
    report = run_evaluation(args.dataset, split=args.split, top_k=args.top_k, min_score=args.min_score,
                            mode=args.mode, apply_policy=args.apply_policy, verify_evidence=args.verify_evidence,
                            rerank_concepts=args.rerank_concepts,
                            output=args.output)
    print(json.dumps({k: v for k, v in report.items() if k != 'questions'}, ensure_ascii=False, indent=2)
          if args.summary else json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
