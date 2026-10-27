import unittest

from rag.evaluate import evaluate
from rag.policy import assess
from rag.retrieval import load_config


class EvaluationTests(unittest.TestCase):
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
