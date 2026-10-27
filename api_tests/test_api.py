import io
import json
from pathlib import Path
import unittest
from unittest.mock import patch
from fastapi.testclient import TestClient
from PIL import Image
from xray_api import create_app, META_COLS, LABELS

class FakePredictor:
    def __init__(self):
        self.paths = []
        self.fail = False
    def predict(self, path, metadata):
        self.paths.append(Path(path))
        if self.fail:
            raise RuntimeError('Test failure')
        return [{'label': label, 'score': 0.82 if i == 0 else 0.02} for i, label in enumerate(LABELS)]

class ApiTests(unittest.TestCase):
    def setUp(self):
        self.fake = FakePredictor()
        self.loads = 0
        def loader():
            self.loads += 1
            return self.fake, {'device': 'test-only', 'sha256': {'best_model.pt': 'fake'}, 'labels': LABELS}
        self.client = TestClient(create_app(loader))
        self.client.__enter__()
        self.meta = {k: 0 for k in META_COLS}
        self.meta.update(age=48, gender='F')
        b = io.BytesIO()
        Image.new('RGB', (20, 20)).save(b, format='PNG')
        self.png = b.getvalue()
    def tearDown(self):
        self.client.__exit__(None, None, None)
    def send(self, meta=None, payload=None, name='image.png'):
        return self.client.post('/predict', data={'metadata': json.dumps(self.meta if meta is None else meta)},
                                files={'file': (name, self.png if payload is None else payload, 'image/png')})
    def test_success_and_single_load(self):
        for _ in range(2):
            r = self.send()
            self.assertEqual(r.status_code, 200, r.text)
            self.assertEqual(r.json()['top1'], 'no-tumor')
            self.assertEqual(len(r.json()['scores']), 10)
            self.assertEqual(len(r.json()['top3']), 3)
        self.assertEqual(self.loads, 1)
        self.assertTrue(all(not p.exists() for p in self.fake.paths))
    def test_health(self):
        self.assertEqual(self.client.get('/health').json()['device'], 'test-only')
        self.assertEqual(len(self.client.get('/metadata-schema').json()['required_fields']), 22)
    def test_missing_extra_invalid_metadata(self):
        for key, value in [('age', None), ('gender', 'X'), ('tibia', 2), ('age', True), ('age', float('nan'))]:
            meta = dict(self.meta, **{key: value})
            self.assertEqual(self.send(meta).status_code, 422)
        self.assertEqual(self.send(dict(self.meta, tumor=1)).status_code, 422)
        del self.meta['age']
        self.assertEqual(self.send().status_code, 422)
    def test_bad_json(self):
        for raw in ['{', '[]', '{"age":48,"age":12}']:
            r = self.client.post('/predict', data={'metadata': raw}, files={'file': ('x.png', self.png)})
            self.assertEqual(r.status_code, 422)
    def test_empty_corrupt_unsupported(self):
        self.assertEqual(self.send(payload=b'').status_code, 422)
        self.assertEqual(self.send(payload=b'fake jpeg').status_code, 415)
        self.assertEqual(self.send(name='x.pdf').status_code, 415)
    def test_large_bytes(self):
        with patch('xray_api.MAX_BYTES', 10):
            self.assertEqual(self.send().status_code, 413)
    def test_large_pixels(self):
        with patch('xray_api.MAX_PIXELS', 10):
            self.assertEqual(self.send().status_code, 413)
    def test_error_cleanup_and_recovery(self):
        self.fake.fail = True
        r = self.send()
        self.assertEqual(r.status_code, 500)
        self.assertNotIn('Test failure', r.text)
        self.assertTrue(all(not p.exists() for p in self.fake.paths))
        self.fake.fail = False
        self.assertEqual(self.send().status_code, 200)
    def test_busy(self):
        original = self.fake.predict
        def nested(path, meta):
            self.assertEqual(self.send().status_code, 429)
            return original(path, meta)
        self.fake.predict = nested
        self.assertEqual(self.send().status_code, 200)
    def test_startup_failure(self):
        def bad():
            raise RuntimeError('Missing checkpoint')
        with self.assertRaises(RuntimeError):
            with TestClient(create_app(bad)):
                pass

if __name__ == '__main__':
    unittest.main()
