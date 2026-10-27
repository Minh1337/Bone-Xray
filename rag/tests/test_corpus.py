import hashlib
import json
import unittest
from pathlib import Path

from rag.build_corpus import extract_blocks, chunks_for


ROOT = Path(__file__).resolve().parents[1] / 'data'


class CorpusTests(unittest.TestCase):
    def test_short_symptom_list_items_are_preserved(self):
        source = {'id': 'test', 'title': 'Test', 'url': 'https://example.org', 'authors': 'Test'}
        blocks = extract_blocks('<main><h2>Symptoms</h2><ul><li>Pain</li><li>Swelling</li></ul></main>')
        chunks = chunks_for(source, blocks, 'hash', 'date', None)
        self.assertEqual(chunks[0]['text'], 'Pain\nSwelling')

    def test_reference_heading_h6_excluded_and_next_section_resumes(self):
        html = ('<main><h2>Diagnosis</h2><p>Biopsy checks tissue for cancer and supports diagnosis.</p>'
                '<h6>References</h6><ol><li>Author 2020. A bibliography entry should not be retrieved.</li></ol>'
                '<h2>Symptoms</h2><p>Persistent pain requires assessment by a trained clinician.</p></main>')
        source = {'id': 'test', 'title': 'Test', 'url': 'https://example.org', 'authors': 'Test'}
        chunks = chunks_for(source, extract_blocks(html), 'hash', 'date', None)
        self.assertEqual([c['section'] for c in chunks], ['Diagnosis', 'Symptoms'])
        self.assertNotIn('bibliography', ' '.join(c['text'] for c in chunks))

    def test_nested_blocks_and_table_cells_do_not_join_words(self):
        blocks = extract_blocks('<main><ul><li><p>First sentence.</p><p>Second sentence.</p></li></ul>'
                                '<table><tr><th>Test</th><td>Biopsy</td></tr></table></main>')
        self.assertEqual(blocks, [('li', 'First sentence. Second sentence.'), ('tr', 'Test Biopsy')])

    def test_parser_keeps_sections_and_discards_scripts(self):
        html = '<main><h1>Bone cancer</h1><p>Primary bone cancer begins in bone tissue.</p>' \
               '<script>alert("ignore")</script><h2>Diagnosis</h2>' \
               '<p>Biopsy examines a tissue sample.</p></main>'
        blocks = extract_blocks(html)
        self.assertEqual(blocks, [('h1', 'Bone cancer'),
                                  ('p', 'Primary bone cancer begins in bone tissue.'),
                                  ('h2', 'Diagnosis'), ('p', 'Biopsy examines a tissue sample.')])

    def test_corpus_provenance_and_evaluation_links(self):
        sources = json.loads((ROOT / 'sources.json').read_text(encoding='utf-8'))
        lock = json.loads((ROOT / 'source_lock.json').read_text(encoding='utf-8'))
        rows = [json.loads(line) for line in (ROOT / 'corpus.jsonl').read_text(encoding='utf-8').splitlines()]
        questions = json.loads((ROOT / 'evaluation_questions.json').read_text(encoding='utf-8'))
        self.assertGreaterEqual(len(sources), 10)
        self.assertEqual({s['id'] for s in sources}, {s['id'] for s in lock})
        self.assertEqual({s['id'] for s in sources}, {r['source_id'] for r in rows})
        self.assertEqual(len(rows), len({r['chunk_id'] for r in rows}))
        for row in rows:
            self.assertEqual(row['text_sha256'], hashlib.sha256(row['text'].encode('utf-8')).hexdigest())
            self.assertTrue(row['section'])
            self.assertTrue(row['authors'])
            self.assertIn('source_date', row)
            self.assertTrue(row['url'].startswith('https://www.cancer.gov/'))
        locations = {(row['source_id'], row['section']) for row in rows}
        for question in questions:
            if question['source_id']:
                self.assertIn((question['source_id'], question['section']), locations)
            else:
                self.assertIn(question['expected_behavior'], {'insufficient_evidence', 'out_of_scope'})

    def test_expanded_evaluation_has_real_evidence_and_disjoint_splits(self):
        dataset = json.loads((ROOT / 'evaluation_v2.json').read_text(encoding='utf-8'))
        self.assertEqual(dataset['corpus_sha256'], hashlib.sha256((ROOT / 'corpus.jsonl').read_bytes()).hexdigest())
        corpus = {row['text_sha256']: row for row in
                  (json.loads(line) for line in (ROOT / 'corpus.jsonl').read_text(encoding='utf-8').splitlines())}
        questions = dataset['questions']
        self.assertEqual(len(questions), len({q['id'] for q in questions}))
        self.assertEqual(len(questions), len({q['question_vi'] for q in questions}))
        self.assertEqual({q['split'] for q in questions}, {'dev', 'test'})
        for question in questions:
            for evidence in question['evidence']:
                row = corpus[evidence['text_sha256']]
                self.assertEqual(row['source_id'], evidence['source_id'])
                self.assertEqual(row['section'], evidence['section'])
                self.assertIn(question['evidence_quote'], row['text'])


if __name__ == '__main__':
    unittest.main()
