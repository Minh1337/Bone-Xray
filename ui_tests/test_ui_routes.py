import importlib
import sys
import unittest
from fastapi.testclient import TestClient
from unittest.mock import patch
import xray_api

class UIRouteTests(unittest.TestCase):
    def test_ui_and_api_together(self):
        # No real checkpoint is loaded here. Real model loads when the server starts.
        fake_app = xray_api.create_app(lambda:(object(), {'device': 'test-only', 'sha256': {}, 'labels': xray_api.LABELS}))
        with patch.object(xray_api, 'app', fake_app):
            sys.modules.pop('xray_ui', None)
            module = importlib.import_module('xray_ui')
            with TestClient(module.app) as client:
                self.assertEqual(client.get('/').status_code, 200)
                self.assertIn('BoneScope', client.get('/').text)
                self.assertEqual(client.get('/history').status_code, 200)
                self.assertEqual(client.get('/dashboard').status_code, 200)
                self.assertEqual(client.get('/ui-assets/app.js').status_code, 200)
                self.assertEqual(client.get('/ui-assets/style.css').status_code, 200)
                self.assertEqual(client.get('/health').json()['status'], 'ready')
                self.assertEqual(client.get('/metadata-schema').status_code, 200)
                self.assertEqual(client.get('/model/best_model.pt').status_code, 404)
                self.assertEqual(client.get('/ui-assets/../model/best_model.pt').status_code, 404)
                self.assertIn('/predict', client.get('/openapi.json').json()['paths'])
            sys.modules.pop('xray_ui', None)

if __name__ == '__main__':
    unittest.main()
