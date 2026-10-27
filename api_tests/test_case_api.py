import unittest
from fastapi.testclient import TestClient
import xray_ui
import database as db

class CaseApiTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(xray_ui.app)
        db.init_db()

    def test_case_lifecycle(self):
        # 1. Save case
        payload = {
            'image_filename': 'test_case.png',
            'image_sha256': 'a' * 64,
            'metadata': {'age': 30, 'gender': 'M'},
            'scores': {'no-tumor': 0.85, 'osteosarcoma': 0.15},
            'top1': 'no-tumor',
            'top1_score': 0.85,
            'prediction_seconds': 0.05,
            'device': 'cuda',
            'model_sha256': 'b' * 64,
            'api_version': '0.1.0'
        }
        r = self.client.post('/cases', json=payload)
        self.assertEqual(r.status_code, 200)
        case_data = r.json()
        case_id = case_data['id']
        self.assertEqual(case_data['top1_label'], 'no-tumor')

        # 2. Get case
        r = self.client.get(f'/cases/{case_id}')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()['image_filename'], 'test_case.png')

        # 3. Add comment
        r = self.client.post(f'/cases/{case_id}/comments', json={'content': 'Bệnh nhân có tiền sử đau khớp'})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()['content'], 'Bệnh nhân có tiền sử đau khớp')

        # 4. Add correction
        r = self.client.post(f'/cases/{case_id}/corrections', json={'corrected_label': 'osteosarcoma', 'reason': 'Sinh thiết xác nhận'})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()['corrected_label'], 'osteosarcoma')

        # 5. Invalid correction label rejected
        r = self.client.post(f'/cases/{case_id}/corrections', json={'corrected_label': 'unknown-disease', 'reason': 'test'})
        self.assertEqual(r.status_code, 422)

        # 6. Check dashboard stats
        r = self.client.get('/dashboard/stats')
        self.assertEqual(r.status_code, 200)
        stats = r.json()
        self.assertGreaterEqual(stats['total_cases'], 1)
        self.assertGreaterEqual(stats['corrected_cases'], 1)

        # 7. List cases
        r = self.client.get('/cases')
        self.assertEqual(r.status_code, 200)
        self.assertGreaterEqual(r.json()['total'], 1)

        # 8. Delete case
        r = self.client.delete(f'/cases/{case_id}')
        self.assertEqual(r.status_code, 200)

        # 9. Verify deleted
        r = self.client.get(f'/cases/{case_id}')
        self.assertEqual(r.status_code, 404)

if __name__ == '__main__':
    unittest.main()
