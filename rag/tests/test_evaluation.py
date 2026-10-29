import json
import tempfile
import unittest
from pathlib import Path

from rag.evaluate import evaluate, run_evaluation
from rag.policy import assess
from rag import retrieval as r
from rag.retrieval import load_config


class EvaluationTests(unittest.TestCase):
    def test_alternative_evidence_groups_are_not_merged_into_one_gold_set(self):
        def row(chunk_id, score):
            return {'source_id': 's', 'section': 'A', 'text_sha256': chunk_id, 'chunk_id': chunk_id,
                    'url': 'https://example.org', 'score': score, 'ranking_score': score,
                    'retrieval_mode': 'dense'}

        first_required, second_required = row('g1', .9), row('g2', .8)
        alternative, distractor = row('g3', .7), row('x', .6)

        class Engine:
            corpus_rows = [first_required, second_required, alternative, distractor]
            def search(self, *args, **kwargs):
                return [distractor, alternative]

        question = {'id': 'alternatives', 'question_vi': 'q',
                    'evidence_groups': [[first_required, second_required], [alternative]]}
        report = evaluate([question], Engine(), top_k=2)
        result = report['questions'][0]
        self.assertEqual(result['evidence_alternative_group_count'], 2)
        self.assertEqual(result['selected_evidence_group'], 1)
        self.assertEqual(result['evidence_group_rank'], 2)
        self.assertEqual(result['complete_evidence_group_count'], 1)
        self.assertEqual(result['evidence_recall_at_k'], 1)
        self.assertEqual(result['evidence_precision_at_k'], .5)
        self.assertEqual(report['evidence_group_completion_at_k'], 1)
        self.assertEqual(report['evidence_group_completion_mrr'], .5)

    def test_exact_gold_chunk_precision_recall_and_ndcg(self):
        def row(chunk_id, score):
            return {'source_id': 's', 'section': 'A', 'text_sha256': chunk_id, 'chunk_id': chunk_id,
                    'url': 'https://example.org', 'score': score, 'ranking_score': score,
                    'retrieval_mode': 'dense'}
        gold_first, distractor, gold_second = row('g1', .9), row('x', .8), row('g2', .7)

        class Engine:
            corpus_rows = [gold_first, distractor, gold_second]
            def search(self, *args, **kwargs):
                return [gold_first, distractor]

        report = evaluate([{'id': 'multi', 'question_vi': 'q', 'evidence': [gold_first, gold_second]}],
                          Engine(), top_k=2)
        self.assertEqual(report['evidence_question_count'], 1)
        self.assertEqual(report['evidence_precision_at_k'], .5)
        self.assertEqual(report['evidence_recall_at_k'], .5)
        self.assertAlmostEqual(report['evidence_ndcg_at_k'], 1 / (1 + 1 / 1.584962500721156))
        self.assertEqual(report['questions'][0]['retrieved_gold_count'], 1)

    def test_reports_routing_confusion_and_answerability_error_counts(self):
        rows = [
            {'source_id': 's', 'section': 'A', 'text_sha256': 'h1', 'chunk_id': 'a',
             'url': 'https://example.org', 'score': 0.9, 'ranking_score': 0.9, 'retrieval_mode': 'dense'},
            {'source_id': 's', 'section': 'B', 'text_sha256': 'h2', 'chunk_id': 'b',
             'url': 'https://example.org', 'score': 0.8, 'ranking_score': 0.8, 'retrieval_mode': 'dense'},
        ]

        class Engine:
            corpus_rows = rows
            def search(self, question, **kwargs):
                return [rows[0]] if question == 'negative with hit' else []

        questions = [
            {'id': 'n', 'question_vi': 'negative with hit', 'expected_status': 'insufficient_evidence'},
            {'id': 'p', 'question_vi': 'positive no hit', 'evidence': [rows[1]]},
        ]
        report = evaluate(questions, Engine())
        self.assertEqual(report['routing_confusion_matrix'], {
            'insufficient_evidence': {'candidates_found': 1},
            'candidates_found': {'insufficient_evidence': 1},
        })
        self.assertEqual(report['negative_with_candidates_count'], 1)
        self.assertEqual(report['negative_with_candidates_denominator'], 1)
        self.assertEqual(report['positive_without_candidates_count'], 1)
        self.assertEqual(report['positive_without_candidates_denominator'], 1)

    def test_three_level_labels_report_disjoint_populations(self):
        row = {'source_id': 's', 'section': 'A', 'text_sha256': 'h', 'chunk_id': 'a',
               'url': 'https://example.org', 'score': 0.9, 'ranking_score': 0.9,
               'retrieval_mode': 'dense'}

        class Engine:
            corpus_rows = [row]

            def search(self, question, **kwargs):
                return [row] if question in {'full', 'partial'} else []

        questions = [
            {'id': 'full', 'question_vi': 'full', 'answerability': 'answerable',
             'expected_status': 'candidates_found', 'evidence': [row]},
            {'id': 'partial', 'question_vi': 'partial', 'answerability': 'partially_answerable',
             'expected_status': 'insufficient_evidence', 'evidence': [row]},
            {'id': 'unsupported', 'question_vi': 'unsupported', 'answerability': 'unanswerable',
             'expected_status': 'insufficient_evidence'},
            {'id': 'oos', 'question_vi': 'oos', 'answerability': 'unanswerable',
             'expected_status': 'out_of_scope'},
        ]
        report = evaluate(questions, Engine())

        self.assertEqual(report['answerability_label_mode'], 'reviewer_three_level')
        self.assertEqual((report['fully_answerable_count'], report['partially_answerable_count'],
                          report['in_scope_unanswerable_count'], report['out_of_scope_count']), (1, 1, 1, 1))
        self.assertEqual(report['answerable_count'], 1)
        self.assertEqual(report['negative_count'], 1)
        self.assertEqual(report['positive_abstention'], 0)
        self.assertEqual(report['negative_abstention'], 1)
        self.assertEqual(report['partially_answerable_candidates_found_count'], 1)
        self.assertEqual(report['partially_answerable_insufficient_evidence_denominator'], 1)
        self.assertEqual(report['partially_answerable_raw_hit_count'], 1)
        self.assertEqual(report['out_of_scope_correct_route_count'], 0)
        self.assertEqual(report['out_of_scope_route_denominator'], 1)
        self.assertEqual(report['evidence_question_count'], 1)
        self.assertEqual(report['evidence_metrics_by_population']['partially_answerable']['question_count'], 1)
        self.assertEqual(report['questions'][1]['evaluation_population'], 'partially_answerable')
        self.assertEqual(report['questions'][3]['evaluation_population'], 'out_of_scope')

    def test_three_level_labels_fail_closed_for_partial_records(self):
        class Engine:
            corpus_rows = []

            def search(self, *args, **kwargs):
                return []

        partial = {'id': 'partial', 'question_vi': 'q', 'answerability': 'partially_answerable',
                   'expected_status': 'candidates_found'}
        with self.assertRaisesRegex(ValueError, 'Inconsistent answerability/expected_status'):
            evaluate([partial], Engine())

    def test_three_level_labels_require_complete_valid_schema(self):
        class Engine:
            corpus_rows = []

            def search(self, *args, **kwargs):
                return []

        labelled = {'id': 'labelled', 'question_vi': 'q', 'answerability': 'unanswerable',
                    'expected_status': 'insufficient_evidence'}
        legacy = {'id': 'legacy', 'question_vi': 'q', 'expected_status': 'insufficient_evidence'}
        with self.assertRaisesRegex(ValueError, 'answerability on every question'):
            evaluate([labelled, legacy], Engine())
        invalid = {**labelled, 'answerability': 'maybe'}
        with self.assertRaisesRegex(ValueError, 'Invalid answerability label'):
            evaluate([invalid], Engine())
        invalid_type = {**labelled, 'answerability': []}
        with self.assertRaisesRegex(ValueError, 'Invalid answerability label'):
            evaluate([invalid_type], Engine())
        missing_status = {'id': 'missing-status', 'question_vi': 'q', 'answerability': 'unanswerable'}
        with self.assertRaisesRegex(ValueError, 'Invalid or missing expected_status'):
            evaluate([missing_status], Engine())
        invalid_status_type = {**labelled, 'expected_status': []}
        with self.assertRaisesRegex(ValueError, 'Invalid or missing expected_status'):
            evaluate([invalid_status_type], Engine())
        missing_gold = {'id': 'answerable-without-gold', 'question_vi': 'q',
                        'answerability': 'answerable', 'expected_status': 'candidates_found'}
        with self.assertRaisesRegex(ValueError, 'Fully answerable item requires gold evidence'):
            evaluate([missing_gold], Engine())

    def test_legacy_evaluation_keeps_legacy_label_mode(self):
        class Engine:
            corpus_rows = []

            def search(self, *args, **kwargs):
                return []

        report = evaluate([{'id': 'legacy', 'question_vi': 'q',
                            'expected_status': 'insufficient_evidence'}], Engine())
        self.assertNotIn('answerability_label_mode', report)
        self.assertEqual(report['answerable_count'], 0)
        self.assertEqual(report['negative_count'], 1)
        self.assertNotIn('answerability', report['questions'][0])

    def test_run_evaluation_rejects_mixed_schema_even_outside_selected_split(self):
        class Engine:
            corpus_rows = []

            def search(self, *args, **kwargs):
                return []

        dataset = {
            'corpus_sha256': r.sha256(r.CORPUS),
            'questions': [
                {'id': 'labelled-dev', 'question_vi': 'q', 'split': 'dev',
                 'answerability': 'unanswerable', 'expected_status': 'insufficient_evidence'},
                {'id': 'legacy-test', 'question_vi': 'q', 'split': 'test',
                 'expected_status': 'insufficient_evidence'},
            ],
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'mixed.json'
            path.write_text(json.dumps(dataset), encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'answerability on every question'):
                run_evaluation(path, engine=Engine(), split='dev')

    def test_same_section_without_answer_evidence_is_not_a_hit(self):
        row = {'source_id': 'source', 'section': 'Diagnosis', 'text_sha256': 'unrelated', 'chunk_id': 'a',
               'url': 'https://example.org', 'score': 0.9, 'ranking_score': 0.9, 'retrieval_mode': 'dense'}
        gold = {**row, 'text_sha256': 'answer'}

        class Engine:
            corpus_rows = [row, gold]
            def search(self, *args, **kwargs):
                return [row]

        q = {'id': 'q', 'question_vi': 'Câu hỏi', 'evidence': [gold]}
        report = evaluate([q], Engine())
        self.assertEqual(report['recall_at_k'], 0)
        self.assertIsNone(report['negative_abstention'])

    def test_general_education_not_confused_with_personal_treatment(self):
        config = load_config()
        for question in ['Các phương pháp điều trị Ewing sarcoma là gì?',
                         'Sinh thiết u xương có vai trò gì?',
                         'What is high-dose chemotherapy for Ewing sarcoma?']:
            self.assertEqual(assess(question, config), (None, None))

    def test_gold_evidence_must_match_its_chunk_id(self):
        row = {'source_id': 'source', 'section': 'Diagnosis', 'text_sha256': 'same-hash', 'chunk_id': 'actual',
               'url': 'https://example.org', 'score': 0.9, 'ranking_score': 0.9, 'retrieval_mode': 'dense'}

        class Engine:
            corpus_rows = [row]
            def search(self, *args, **kwargs):
                return [row]

        question = {'id': 'stale', 'question_vi': 'Câu hỏi', 'evidence': [
            {'chunk_id': 'old-id', 'source_id': 'source', 'section': 'Diagnosis', 'text_sha256': 'same-hash'}]}
        with self.assertRaisesRegex(ValueError, 'Gold evidence missing or changed: stale'):
            evaluate([question], Engine())
