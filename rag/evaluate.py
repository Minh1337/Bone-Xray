"""Evaluate raw retrieval and query routing separately; persist reproducible results."""

import argparse
import json
import math
from datetime import datetime, timezone
from pathlib import Path

try:
    from rag import retrieval as r
except ModuleNotFoundError:
    import retrieval as r


ANSWERABILITY_VALUES = {'answerable', 'partially_answerable', 'unanswerable'}
EXPECTED_STATUS_VALUES = {'candidates_found', 'insufficient_evidence', 'out_of_scope'}


def _validate_answerability_labels(questions):
    """Validate an all-or-none reviewer label schema; preserve legacy datasets unchanged."""
    has_labels = ['answerability' in q for q in questions]
    if any(has_labels) and not all(has_labels):
        raise ValueError('Three-level evaluation requires answerability on every question')
    if not has_labels or not has_labels[0]:
        return False

    for q in questions:
        answerability = q.get('answerability')
        expected_status = q.get('expected_status')
        if not isinstance(answerability, str) or answerability not in ANSWERABILITY_VALUES:
            raise ValueError(f"Invalid answerability label for {q.get('id', '<missing id>')}: {answerability!r}")
        if not isinstance(expected_status, str) or expected_status not in EXPECTED_STATUS_VALUES:
            raise ValueError(f"Invalid or missing expected_status for {q.get('id', '<missing id>')}")
        valid_statuses = {
            'answerable': {'candidates_found'},
            'partially_answerable': {'insufficient_evidence'},
            'unanswerable': {'insufficient_evidence', 'out_of_scope'},
        }[answerability]
        if expected_status not in valid_statuses:
            raise ValueError(
                f"Inconsistent answerability/expected_status for {q.get('id', '<missing id>')}: "
                f"{answerability!r}/{expected_status!r}"
            )
        if answerability == 'answerable':
            has_exact_evidence = bool(q.get('evidence') or q.get('evidence_groups'))
            has_source_target = all(isinstance(q.get(key), str) and q[key].strip()
                                    for key in ('source_id', 'section'))
            if not (has_exact_evidence or has_source_target):
                raise ValueError(
                    f"Fully answerable item requires gold evidence: {q.get('id', '<missing id>')}"
                )
    return True


def _evidence_metric_summary(items):
    evidence_questions = [x for x in items if x['gold_evidence_count']]
    return {
        'question_count': len(evidence_questions),
        'precision_at_k': (sum(x['evidence_precision_at_k'] for x in evidence_questions)
                           / len(evidence_questions) if evidence_questions else None),
        'recall_at_k': (sum(x['evidence_recall_at_k'] for x in evidence_questions)
                        / len(evidence_questions) if evidence_questions else None),
        'ndcg_at_k': (sum(x['evidence_ndcg_at_k'] for x in evidence_questions)
                      / len(evidence_questions) if evidence_questions else None),
    }


def evaluate(questions, engine, *, top_k=5, min_score=None, mode='dense', apply_policy=False,
             verify_evidence=False, rerank_concepts=False):
    if top_k < 1:
        raise ValueError('top_k must be at least 1')
    if (verify_evidence or rerank_concepts) and not apply_policy:
        raise ValueError('Evidence checking requires apply_policy=True')
    three_level_labels = _validate_answerability_labels(questions)
    results = []
    available = {(row['chunk_id'], row['source_id'], row['section'], row['text_sha256'])
                 for row in engine.corpus_rows}
    for q in questions:
        explicit_evidence_groups = 'evidence_groups' in q
        if 'evidence' in q and 'evidence_groups' in q:
            raise ValueError(f"Use either evidence or evidence_groups, not both: {q['id']}")
        if explicit_evidence_groups:
            groups = q['evidence_groups']
            if (not isinstance(groups, list) or not groups
                    or any(not isinstance(group, list) or not group for group in groups)):
                raise ValueError(f"Evidence groups must be a non-empty list of non-empty lists: {q['id']}")
        else:
            legacy_evidence = q.get('evidence', [])
            groups = [legacy_evidence] if legacy_evidence else []
        targets = [item for group in groups for item in group]
        if any(not isinstance(x, dict)
               or not all(key in x for key in ('chunk_id', 'source_id', 'section', 'text_sha256'))
               or any(not isinstance(x[key], str) or not x[key].strip()
                      for key in ('chunk_id', 'source_id', 'section', 'text_sha256'))
               or (x['chunk_id'], x['source_id'], x['section'], x['text_sha256']) not in available
               for x in targets):
            raise ValueError(f"Gold evidence missing or changed: {q['id']}")
        group_keys = [
            [(x['chunk_id'], x['source_id'], x['section'], x['text_sha256']) for x in group]
            for group in groups
        ]
        if any(len(keys) != len(set(keys)) for keys in group_keys):
            raise ValueError(f"Duplicate evidence item within a group: {q['id']}")
        if apply_policy:
            response = r.retrieve(q['question_vi'], engine=engine, top_k=top_k,
                                  min_score=min_score, mode=mode, verify_evidence=verify_evidence,
                                  rerank_concepts=rerank_concepts)
            hits = response['hits']
            status, reason = response['status'], response['reason']
            preferred_source_id = response.get('preferred_source_id')
            preferred_section = response.get('preferred_section')
        else:
            hits = engine.search(q['question_vi'], top_k=top_k, min_score=min_score, mode=mode)
            status, reason = ('candidates_found' if hits else 'insufficient_evidence'), 'raw_retrieval'
            preferred_source_id = None
            preferred_section = None
        answerability = q.get('answerability') if three_level_labels else None
        answerable = (answerability == 'answerable' if three_level_labels
                      else bool(groups or q.get('source_id')))
        evidence_group_rank = None
        complete_evidence_group_count = 0 if explicit_evidence_groups else None
        evidence_list_completion_rank = None
        evidence_list_complete = None
        selected_group_index = None
        if groups:
            retrieved_keys = [(h['chunk_id'], h['source_id'], h['section'], h['text_sha256']) for h in hits]
            accepted_keys = set(key for group in group_keys for key in group)
            rank = next((i + 1 for i, key in enumerate(retrieved_keys) if key in accepted_keys), None)
            group_scores = []
            for group_index, wanted_list in enumerate(group_keys):
                wanted = set(wanted_list)
                retrieved_gold = {key for key in retrieved_keys[:top_k] if key in wanted}
                recall = len(retrieved_gold) / len(wanted)
                precision = len(retrieved_gold) / top_k
                dcg = sum(1 / math.log2(i + 2) for i, key in enumerate(retrieved_keys[:top_k])
                          if key in wanted)
                ideal_dcg = sum(1 / math.log2(i + 2) for i in range(min(len(wanted), top_k)))
                ndcg = dcg / ideal_dcg if ideal_dcg else None
                completion_rank = next((i for i in range(len(wanted_list), len(retrieved_keys) + 1)
                                        if wanted.issubset(set(retrieved_keys[:i]))), None)
                if explicit_evidence_groups and completion_rank is not None:
                    complete_evidence_group_count += 1
                    evidence_group_rank = (completion_rank if evidence_group_rank is None
                                           else min(evidence_group_rank, completion_rank))
                group_scores.append((recall, ndcg or 0.0, -group_index, group_index,
                                     precision, retrieved_gold))
            selected = max(group_scores)
            _, _, _, selected_group_index, evidence_precision, retrieved_gold = selected
            evidence_recall = selected[0]
            evidence_ndcg = selected[1]
            if not explicit_evidence_groups:
                legacy_gold = set(group_keys[0])
                evidence_list_completion_rank = next((i for i in range(len(group_keys[0]),
                                                                       len(retrieved_keys) + 1)
                                                      if legacy_gold.issubset(set(retrieved_keys[:i]))), None)
                evidence_list_complete = evidence_list_completion_rank is not None
        elif q.get('source_id'):
            rank = next((i + 1 for i, h in enumerate(hits)
                         if h['source_id'] == q['source_id'] and h['section'] == q['section']), None)
            evidence_recall = evidence_precision = evidence_ndcg = None
            retrieved_gold = set()
        else:
            rank = None
            evidence_recall = evidence_precision = evidence_ndcg = None
            retrieved_gold = set()
        expected_status = (q['expected_status'] if three_level_labels else
                           q.get('expected_status', 'candidates_found' if answerable else
                                 q.get('expected_behavior', 'insufficient_evidence')))
        item = {'id': q['id'], 'split': q.get('split', 'regression'),
                'answerable': answerable, 'rank': rank, 'expected_status': expected_status,
                'status': status, 'reason': reason, 'status_match': status == expected_status,
                'preferred_source_id': preferred_source_id, 'preferred_section': preferred_section,
                'hits': len(hits), 'evidence_check': response.get('evidence_check') if apply_policy else None,
                'gold_evidence_count': (len(group_keys[selected_group_index])
                                        if groups and selected_group_index is not None else 0),
                'explicit_evidence_groups': explicit_evidence_groups,
                'evidence_alternative_group_count': len(groups) if explicit_evidence_groups else None,
                'selected_evidence_group': selected_group_index if explicit_evidence_groups else None,
                'complete_evidence_group_count': complete_evidence_group_count,
                'evidence_group_rank': evidence_group_rank,
                'evidence_list_complete': evidence_list_complete,
                'evidence_list_completion_rank': evidence_list_completion_rank,
                'retrieved_gold_count': len(retrieved_gold),
                'evidence_precision_at_k': evidence_precision,
                'evidence_recall_at_k': evidence_recall,
                'evidence_ndcg_at_k': evidence_ndcg,
                'retrieved': [
                    {key: h[key] for key in ('chunk_id', 'source_id', 'section', 'text_sha256',
                                            'url', 'score', 'ranking_score', 'retrieval_mode')}
                    for h in hits]}
        if three_level_labels:
            item['answerability'] = answerability
            item['evaluation_population'] = (
                'fully_answerable' if answerability == 'answerable' else
                'partially_answerable' if answerability == 'partially_answerable' else
                'out_of_scope' if expected_status == 'out_of_scope' else
                'in_scope_unanswerable'
            )
        results.append(item)
    positive = [x for x in results if x['answerable']]
    partial = [x for x in results if x.get('evaluation_population') == 'partially_answerable']
    out_of_scope = [x for x in results if x.get('evaluation_population') == 'out_of_scope']
    negative = ([x for x in results if x.get('evaluation_population') == 'in_scope_unanswerable']
                if three_level_labels else [x for x in results if not x['answerable']])
    routing_confusion = {}
    for item in results:
        expected = item['expected_status']
        predicted = item['status']
        routing_confusion.setdefault(expected, {})
        routing_confusion[expected][predicted] = routing_confusion[expected].get(predicted, 0) + 1
    evidence_questions = ([x for x in positive if x['gold_evidence_count']] if three_level_labels else
                          [x for x in results if x['gold_evidence_count']])
    explicit_group_questions = [x for x in evidence_questions if x['explicit_evidence_groups']]
    legacy_evidence_list_questions = [x for x in evidence_questions if not x['explicit_evidence_groups']]
    report = {
        'answerable_count': len(positive), 'negative_count': len(negative),
        'recall_at_k': sum(x['rank'] is not None for x in positive) / len(positive) if positive else None,
        'mrr_at_k': sum(1 / x['rank'] for x in positive if x['rank']) / len(positive) if positive else None,
        'negative_abstention': sum(x['hits'] == 0 for x in negative) / len(negative) if negative else None,
        'positive_abstention': sum(x['hits'] == 0 for x in positive) / len(positive) if positive else None,
        # These are query-set diagnostic counts, not population risk estimates.
        'negative_with_candidates_count': sum(x['hits'] > 0 for x in negative),
        'negative_with_candidates_denominator': len(negative),
        'positive_without_candidates_count': sum(x['hits'] == 0 for x in positive),
        'positive_without_candidates_denominator': len(positive),
        'routing_accuracy': sum(x['status_match'] for x in results) / len(results) if results else None,
        'routing_confusion_matrix': routing_confusion,
        'evidence_question_count': len(evidence_questions),
        'evidence_group_question_count': len(explicit_group_questions),
        'evidence_alternative_group_count': sum(x['evidence_alternative_group_count']
                                                 for x in explicit_group_questions),
        'evidence_group_completion_at_k': (
            sum(x['evidence_group_rank'] is not None for x in explicit_group_questions)
            / len(explicit_group_questions) if explicit_group_questions else None),
        'evidence_group_completion_mrr': (
            sum(1 / x['evidence_group_rank'] for x in explicit_group_questions if x['evidence_group_rank'])
            / len(explicit_group_questions) if explicit_group_questions else None),
        'legacy_evidence_list_question_count': len(legacy_evidence_list_questions),
        'legacy_evidence_list_completion_at_k': (
            sum(x['evidence_list_complete'] for x in legacy_evidence_list_questions)
            / len(legacy_evidence_list_questions) if legacy_evidence_list_questions else None),
        'legacy_evidence_list_completion_mrr': (
            sum(1 / x['evidence_list_completion_rank'] for x in legacy_evidence_list_questions
                if x['evidence_list_completion_rank'])
            / len(legacy_evidence_list_questions) if legacy_evidence_list_questions else None),
        'evidence_precision_at_k': (sum(x['evidence_precision_at_k'] for x in evidence_questions)
                                     / len(evidence_questions) if evidence_questions else None),
        'evidence_recall_at_k': (sum(x['evidence_recall_at_k'] for x in evidence_questions)
                                 / len(evidence_questions) if evidence_questions else None),
        'evidence_ndcg_at_k': (sum(x['evidence_ndcg_at_k'] for x in evidence_questions)
                               / len(evidence_questions) if evidence_questions else None),
        'questions': results,
    }
    if three_level_labels:
        populations = {
            'fully_answerable': positive,
            'partially_answerable': partial,
            'in_scope_unanswerable': negative,
            'out_of_scope': out_of_scope,
        }
        report.update({
            'answerability_label_mode': 'reviewer_three_level',
            'fully_answerable_count': len(positive),
            'partially_answerable_count': len(partial),
            'in_scope_unanswerable_count': len(negative),
            'out_of_scope_count': len(out_of_scope),
            'fully_answerable_candidate_route_count': sum(x['status'] == 'candidates_found' for x in positive),
            'fully_answerable_candidate_route_denominator': len(positive),
            'partially_answerable_insufficient_evidence_count': sum(
                x['status'] == 'insufficient_evidence' for x in partial),
            'partially_answerable_insufficient_evidence_denominator': len(partial),
            'partially_answerable_candidates_found_count': sum(
                x['status'] == 'candidates_found' for x in partial),
            'partially_answerable_raw_hit_count': sum(x['hits'] > 0 for x in partial),
            'partially_answerable_denominator': len(partial),
            'in_scope_unanswerable_insufficient_evidence_count': sum(
                x['status'] == 'insufficient_evidence' for x in negative),
            'in_scope_unanswerable_expected_status_denominator': len(negative),
            'out_of_scope_correct_route_count': sum(x['status'] == 'out_of_scope' for x in out_of_scope),
            'out_of_scope_route_denominator': len(out_of_scope),
            'routing_confusion_by_population': {
                population: {
                    expected: {
                        predicted: sum(x['expected_status'] == expected and x['status'] == predicted
                                       for x in items)
                        for predicted in sorted({x['status'] for x in items})
                    }
                    for expected in sorted({x['expected_status'] for x in items})
                }
                for population, items in populations.items()
            },
            'evidence_metrics_by_population': {
                population: _evidence_metric_summary(items)
                for population, items in populations.items()
            },
        })
    return report


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
    _validate_answerability_labels(questions)
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
        'gold_type': ('chunk_id_source_section_text_hash' if any(q.get('evidence') or q.get('evidence_groups')
                                                                 for q in questions)
                      else 'source_section'),
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
