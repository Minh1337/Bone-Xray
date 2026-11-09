import importlib
import sys
import unittest
from fastapi.testclient import TestClient
from unittest.mock import patch
import bonescope.xray_api as xray_api

class UIRouteTests(unittest.TestCase):
    def test_ui_and_api_together(self):
        # No real checkpoint is loaded here. Real model loads when the server starts.
        fake_app = xray_api.create_app(lambda:(object(), {'device': 'test-only', 'sha256': {}, 'labels': xray_api.LABELS}))
        with patch.object(xray_api, 'app', fake_app):
            sys.modules.pop('bonescope.xray_ui', None)
            module = importlib.import_module('bonescope.xray_ui')
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

    def test_research_studio_ui_and_static_assets_contract(self):
        from rag.demo_api import create_app
        with TestClient(create_app(lambda *_a, **_k: None), base_url='http://127.0.0.1:8765') as client:
            home = client.get('/')
            self.assertEqual(home.status_code, 200)
            self.assertEqual(home.headers.get('cache-control'), 'no-store')
            self.assertEqual(home.headers.get('x-content-type-options'), 'nosniff')
            html = home.text
            for required_hook in (
                'id="attach-image"',
                'id="image-attachment"',
                'id="remove-image-attachment"',
                'id="case-reference-id"',
                'id="case-reference-load"',
                'class="btxrd-sample-chip"',
                'data-btxrd-id="IMG000002"',
                'data-btxrd-id="IMG000240"',
                'class="welcome-ambient"',
                'class="xray-scanline"',
                'class="quick-prompts"',
            ):
                self.assertIn(required_hook, html)

            for asset in ('/assets/style.css', '/assets/studio.css', '/assets/graphite.css', '/assets/app.js'):
                res = client.get(asset)
                self.assertEqual(res.status_code, 200, asset)
                self.assertTrue(len(res.text) > 100, asset)

if __name__ == '__main__':
    unittest.main()
