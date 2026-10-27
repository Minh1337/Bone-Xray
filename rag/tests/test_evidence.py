import hashlib
import json
import unittest
from pathlib import Path

import numpy as np

from rag.evidence import EvidenceVerifier
from rag.retrieval import Retriever, retrieve


def row(identifier, text, title='Chordoma', section='Overview'):
    return {'chunk_id': identifier, 'text': text, 'title': title, 'section': section,
            'source_id': 'test-source', 'url': 'https://example.org/' + identifier,
            'score': 0.8, 'ranking_score': 0.05}


class EvidenceTests(unittest.TestCase):
    def test_retrieval_experiments_preserve_source_filter_and_never_authorize_an_answer(self):
        class Encoder:
            def encode(self, values, **kwargs):
                return np.array([[1, 0] for _ in values], dtype=np.float32)
        hit = row('a', 'A chordoma biopsy is studied under a microscope.')
        other = {**row('b', 'A chordoma biopsy is studied under a microscope.'), 'source_id': 'excluded'}
        engine = Retriever(model=Encoder(), index=([hit, other], np.array([[1, 0], [1, 0]], dtype=np.float32)))
        response = retrieve('Chordoma biopsy microscope?', engine=engine, rerank_concepts=True, source_ids=['test-source'])
        self.assertEqual([h['chunk_id'] for h in response['hits']], ['a'])
        self.assertFalse(response['answer_ready'])
        response = retrieve('Chordoma biopsy zebrafish?', engine=engine, verify_evidence=True)
        self.assertEqual(response['status'], 'insufficient_evidence')
        self.assertEqual(response['hits'], [])
        with self.assertRaises(ValueError):
            retrieve('Chordoma?', engine=engine, verify_evidence=True, rerank_concepts=True)

    def test_where_is_not_misread_as_pain_after_accent_folding(self):
        hit = row('a', 'Chordoma can be found along the spine.')
        checker = EvidenceVerifier([hit])
        self.assertNotIn('pain', checker.parse('Chordoma ở đâu?')['concepts'])
        self.assertIn('pain', checker.parse('Chordoma có gây đau?')['concepts'])
        self.assertIn('sample', checker.parse('mẫu')['concepts'])
        self.assertNotIn('sample', checker.parse('máu')['concepts'])

    def test_heading_cannot_prove_a_requested_medical_fact(self):
        hit = row('a', 'Chordoma is found along the spine.', section='Biopsy')
        checker = EvidenceVerifier([hit])
        hits, reason, diagnostics = checker.check('Chordoma biopsy?', [hit], top_k=5)
        self.assertEqual(hits, [])
        self.assertIn('biopsy', diagnostics['best_missing'])

    def test_all_concepts_must_be_in_the_same_evidence_chunk(self):
        first = row('a', 'Chordoma is a spinal tumor.')
        second = row('b', 'Biopsy samples are examined under a microscope.', title='Other condition')
        checker = EvidenceVerifier([first, second])
        hits, _, _ = checker.check('Chordoma biopsy microscope?', [first, second], top_k=5)
        self.assertEqual(hits, [])

    def test_reranking_keeps_original_citations(self):
        first = row('a', 'Chordoma is a spinal tumor.')
        second = row('b', 'A biopsy of chordoma is examined by a pathologist under a microscope.')
        checker = EvidenceVerifier([first, second])
        hits, _, _ = checker.check('Chordoma biopsy microscope?', [first, second], top_k=5)
        self.assertEqual([h['chunk_id'] for h in hits], ['b'])
        self.assertEqual(hits[0]['url'], second['url'])

    def test_rerank_only_keeps_uncertain_candidates_and_marks_missing_terms(self):
        hit = row('a', 'Chordoma is found along the spine.')
        checker = EvidenceVerifier([hit])
        hits, reason, diagnostics = checker.check('Chordoma biopsy?', [hit], top_k=5, rerank_only=True)
        self.assertEqual(hits[0]['url'], hit['url'])
        self.assertIn('biopsy', hits[0]['evidence_coverage']['missing'])
        self.assertTrue(diagnostics['rerank_only'])

    def test_unknown_terms_are_not_a_hardcoded_treatment_blacklist(self):
        hit = row('a', 'Chordoma treatment is described here.')
        checker = EvidenceVerifier([hit])
        hits, reason, diagnostics = checker.check('Chordoma treatment zebrafish?', [hit], top_k=5)
        self.assertEqual(reason, 'unrecognized_question_terms')
        self.assertIn('zebrafish', diagnostics['unknown_terms'])
        updated = row('b', 'A zebrafish model of chordoma treatment is studied here.')
        checker = EvidenceVerifier([hit, updated])
        hits, _, _ = checker.check('Chordoma treatment zebrafish?', [hit, updated], top_k=5)
        self.assertEqual([h['chunk_id'] for h in hits], ['b'])

    def test_new_stress_evidence_matches_current_corpus(self):
        data = Path(__file__).resolve().parents[1] / 'data'
        dataset = json.loads((data / 'evaluation_evidence_v3.json').read_text(encoding='utf-8'))
        self.assertEqual(dataset['corpus_sha256'], hashlib.sha256((data / 'corpus.jsonl').read_bytes()).hexdigest())
        corpus = {r['text_sha256']: r for r in
                  (json.loads(line) for line in (data / 'corpus.jsonl').read_text(encoding='utf-8').splitlines())}
        for question in dataset['questions']:
            for evidence in question['evidence']:
                self.assertIn(question['evidence_quote'], corpus[evidence['text_sha256']]['text'])


if __name__ == '__main__':
    unittest.main()
