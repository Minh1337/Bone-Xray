import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient
from PIL import Image

import database as db
from case_api import router
from xray_api import LABELS, META_COLS, create_app


class FakePredictor:
    def predict(self, path, metadata):
        return [{'label': label, 'score': 0.82 if i == 0 else 0.02}
                for i, label in enumerate(LABELS)]


class CaseApiTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db_patch = patch.object(db, 'DB_PATH', Path(self.tmp.name) / 'bonescope.db')
        self.db_patch.start()
        db.init_db()
        app = create_app(lambda: (FakePredictor(), {
            'device': 'test-only', 'sha256': {'best_model.pt': 'b' * 64}, 'labels': LABELS
        }))
        app.include_router(router)
        self.client = TestClient(app)
        self.client.__enter__()
        image = io.BytesIO()
        Image.new('RGB', (20, 20)).save(image, format='PNG')
        self.image = image.getvalue()

    def tearDown(self):
        self.client.__exit__(None, None, None)
        self.db_patch.stop()
        self.tmp.cleanup()

    def test_case_lifecycle(self):
        metadata = {key: 0 for key in META_COLS}
        metadata.update(age=30, gender='M')
        prediction = self.client.post('/predict',
            data={'metadata': json.dumps(metadata)},
            files={'file': ('test_case.png', self.image, 'image/png')})
        self.assertEqual(prediction.status_code, 200)
        token = prediction.json()['prediction_id']

        self.assertEqual(self.client.post('/cases', json={'prediction_id': 'x' * 40}).status_code, 422)
        self.assertEqual(self.client.post('/cases', json={
            'prediction_id': token, 'top1': 'osteosarcoma', 'scores': {'osteosarcoma': 1}
        }).status_code, 422)
        self.assertEqual(self.client.post('/cases', json={
            'prediction_id': token, 'true_label': 'not-a-class'
        }).status_code, 422)
        saved = self.client.post('/cases', json={'prediction_id': token})
        self.assertEqual(saved.status_code, 200)
        self.assertEqual(saved.json()['top1_label'], 'no-tumor')
        self.assertEqual(self.client.post('/cases', json={'prediction_id': token}).status_code, 422)

        cases = self.client.get('/cases').json()
        self.assertEqual(cases['total'], 1)
        case_id = cases['cases'][0]['id']
        self.assertEqual(self.client.get(f'/cases/{case_id}').json()['image_filename'], 'test_case.png')

        comment = self.client.post(f'/cases/{case_id}/comments', json={'content': '<img src=x onerror=alert(1)>'})
        self.assertEqual(comment.status_code, 200)
        correction = self.client.post(f'/cases/{case_id}/corrections',
            json={'corrected_label': 'osteosarcoma', 'reason': 'Sinh thiết xác nhận'})
        self.assertEqual(correction.status_code, 200)
        self.assertEqual(self.client.post(f'/cases/{case_id}/corrections',
            json={'corrected_label': 'unknown-disease'}).status_code, 422)

        stats = self.client.get('/dashboard/stats').json()
        self.assertEqual(stats['total_cases'], 1)
        self.assertEqual(stats['corrected_cases'], 1)
        self.assertEqual(self.client.delete(f'/cases/{case_id}').status_code, 200)
        self.assertEqual(self.client.get(f'/cases/{case_id}').status_code, 404)


if __name__ == '__main__':
    unittest.main()
