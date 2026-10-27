import hashlib
import json
import unittest
from pathlib import Path

from rag.build_corpus import extract_blocks


ROOT = Path(__file__).resolve().parents[1] / 'data'


class CorpusTests(unittest.TestCase):
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


if __name__ == '__main__':
    unittest.main()
