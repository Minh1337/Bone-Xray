import json
import tempfile
import unittest
from pathlib import Path

from bonescope.verify_api import hash_basis, load_code_revisions

BASE = {'best_model.pt': 'm1', 'inference.py': 'old', 'model_definition.py': 'd1'}
REV = [{'file': 'inference.py', 'baseline_sha256': 'old', 'accepted_sha256': 'new', 'commit': 'abc'}]


class VerifyApiHashBasisTests(unittest.TestCase):
    def test_baseline_match(self):
        self.assertEqual(set(hash_basis(dict(BASE), BASE, REV).values()), {'baseline'})

    def test_documented_code_revision_is_accepted(self):
        basis = hash_basis({**BASE, 'inference.py': 'new'}, BASE, REV)
        self.assertEqual(basis['inference.py'], 'accepted_revision:abc')

    def test_undocumented_code_change_fails(self):
        self.assertIsNone(hash_basis({**BASE, 'inference.py': 'other'}, BASE, REV)['inference.py'])

    def test_model_artifact_change_never_accepted(self):
        rev = REV + [{'file': 'best_model.pt', 'baseline_sha256': 'm1', 'accepted_sha256': 'm2'}]
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'rev.json'
            path.write_text(json.dumps({'revisions': rev}), encoding='utf-8')
            loaded = load_code_revisions(path)
        self.assertEqual([r['file'] for r in loaded], ['inference.py'])
        self.assertIsNone(hash_basis({**BASE, 'best_model.pt': 'm2'}, BASE, loaded)['best_model.pt'])

    def test_repository_revision_matches_current_inference(self):
        import hashlib
        root = Path(__file__).resolve().parents[1]
        current = hashlib.sha256((root / 'bonescope' / 'inference.py').read_bytes()).hexdigest()
        accepted = {r['accepted_sha256'] for r in load_code_revisions() if r['file'] == 'inference.py'}
        self.assertIn(current, accepted)


if __name__ == '__main__':
    unittest.main()
