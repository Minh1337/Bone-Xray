"""Compare optional lexical evidence coverage with the unchanged hybrid baseline."""

import argparse
import json
from pathlib import Path

try:
    from rag import retrieval as r
    from rag.evaluate import run_evaluation
except ModuleNotFoundError:
    import retrieval as r
    from evaluate import run_evaluation


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=False)  # Never overwrite an earlier experiment.
    engine = r.Retriever()
    summaries = []
    for name, dataset, split in [
        ('regression', 'evaluation_questions.json', 'all'),
        ('v2_dev', 'evaluation_v2.json', 'dev'),
        ('v2_used_test', 'evaluation_v2.json', 'test'),
        ('v3_stress', 'evaluation_evidence_v3.json', 'all'),
    ]:
        for suffix, verify, rerank in [('baseline', False, False), ('rerank', False, True), ('coverage', True, False)]:
            experiment = name + '_' + suffix
            report = run_evaluation(r.DATA / dataset, engine=engine, split=split, mode='hybrid',
                                    apply_policy=True, verify_evidence=verify, rerank_concepts=rerank,
                                    output=args.output_dir / (experiment + '.json'))
            summary = {'experiment': experiment, **{key: report[key] for key in
                       ('answerable_count', 'negative_count', 'recall_at_k', 'mrr_at_k',
                        'negative_abstention', 'positive_abstention', 'routing_accuracy')}}
            summaries.append(summary)
            print(json.dumps(summary), flush=True)
    (args.output_dir / 'summary.json').write_text(json.dumps(summaries, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
