import copy
import tempfile
import unittest
from pathlib import Path
from validation import META_COLS, validate_case, compare_scores

class ValidationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.base = Path(self.tmp.name)
        (self.base / 'test.jpg').write_bytes(b'placeholder')
        self.case = {'id': 'test', 'image': 'test.jpg', 'metadata': {k: 0 for k in META_COLS}}
        self.case['metadata'].update(age=25, gender='M')

    def tearDown(self):
        self.tmp.cleanup()

    def test_valid_schema(self):
        self.assertEqual(validate_case(self.case, self.base)[0].name, 'test.jpg')

    def test_reject_missing_and_invalid_metadata(self):
        for key, value in [('age', None), ('age', float('nan')), ('age', -1), ('age', True), ('gender', 'unknown'), ('hand', 2), ('hand', '0')]:
            with self.subTest(key=key, value=value):
                case = copy.deepcopy(self.case)
                case['metadata'][key] = value
                with self.assertRaises(ValueError):
                    validate_case(case, self.base)
        del self.case['metadata']['age']
        with self.assertRaises(ValueError):
            validate_case(self.case, self.base)

    def test_missing_image(self):
        self.case['image'] = 'missing.jpg'
        with self.assertRaises(ValueError):
            validate_case(self.case, self.base)

    def test_reference_scores(self):
        scores = {'a': 0.7, 'b': 0.3}
        self.assertTrue(compare_scores(scores, scores)['passed'])
        self.assertFalse(compare_scores(scores, {'a': 0.6, 'b': 0.4})['passed'])
        for invalid in [{'a': 1}, {'a': float('nan'), 'b': 0.3}, {'a': 0.8, 'b': 0.8}]:
            with self.assertRaises(ValueError):
                compare_scores(scores, invalid)

if __name__ == '__main__':
    unittest.main()
