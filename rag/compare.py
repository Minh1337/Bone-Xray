"""Run the frozen retrieval comparison with one local model load."""

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
    engine = r.Retriever()
    experiments = [
        ('regression_dense', 'evaluation_questions.json', 'all', 'dense', False),
        ('regression_hybrid_raw', 'evaluation_questions.json', 'all', 'hybrid', False),
        ('regression_hybrid_guarded', 'evaluation_questions.json', 'all', 'hybrid', True),
        ('v2_dev_dense', 'evaluation_v2.json', 'dev', 'dense', False),
        ('v2_dev_hybrid_guarded', 'evaluation_v2.json', 'dev', 'hybrid', True),
        ('v2_test_dense', 'evaluation_v2.json', 'test', 'dense', False),
        ('v2_test_hybrid_guarded', 'evaluation_v2.json', 'test', 'hybrid', True),
    ]
    summaries = []
    for name, dataset, split, mode, policy in experiments:
        report = run_evaluation(r.DATA / dataset, engine=engine, split=split, mode=mode,
                                apply_policy=policy, output=args.output_dir / f'{name}.json')
        summary = {'experiment': name, **{key: report[key] for key in
                   ('answerable_count', 'negative_count', 'recall_at_k', 'mrr_at_k',
                    'negative_abstention', 'positive_abstention', 'routing_accuracy')}}
        summaries.append(summary)
        print(json.dumps(summary), flush=True)
    (args.output_dir / 'summary.json').write_text(json.dumps(summaries, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
