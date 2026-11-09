import math
from pathlib import Path

META_COLS = ['age', 'gender', 'hand', 'ulna', 'radius', 'humerus', 'foot',
             'tibia', 'fibula', 'femur', 'hip bone', 'ankle-joint', 'knee-joint',
             'hip-joint', 'elbow-joint', 'shoulder-joint', 'upper limb',
             'lower limb', 'pelvis', 'frontal', 'lateral', 'oblique']

def validate_case(case, base):
    if not isinstance(case, dict):
        raise ValueError('Each case must be a JSON object')
    if not isinstance(case.get('id'), str) or not case['id'].strip():
        raise ValueError('Missing case id')
    image = case.get('image')
    if not isinstance(image, str) or not image.strip():
        raise ValueError('Missing image path')
    path = (Path(base) / image).resolve()
    if not path.is_file():
        raise ValueError(f'Image not found: {path}')
    if path.suffix.lower() not in {'.png', '.jpg', '.jpeg', '.bmp', '.tif', '.tiff'}:
        raise ValueError('Use a raster image, not DICOM or PDF')
    if path.stat().st_size > 30 * 1024 * 1024:
        raise ValueError('Image exceeds 30 MiB; use the original dataset test image')
    meta = case.get('metadata')
    if not isinstance(meta, dict):
        raise ValueError('metadata must be an object')
    if set(meta) != set(META_COLS):
        raise ValueError(f'Metadata mismatch: missing={sorted(set(META_COLS)-set(meta))}; extra={sorted(set(meta)-set(META_COLS))}')
    age = meta['age']
    if isinstance(age, bool) or not isinstance(age, (int, float)) or not math.isfinite(age) or not 0 <= age <= 120:
        raise ValueError('age must be a finite number from 0 to 120; do not guess missing age')
    if meta['gender'] not in ('M', 'F'):
        raise ValueError('gender must be M or F, matching the dataset')
    for key in META_COLS[2:]:
        if type(meta[key]) not in (int, float) or meta[key] not in (0, 1):
            raise ValueError(f'{key} must be numeric 0 or 1')
    for key in ('expected_top1', 'true_label'):
        if case.get(key) is not None and not isinstance(case[key], str):
            raise ValueError(f'{key} must be a label string or null')
    return path, meta

def compare_scores(actual, expected, tolerance=1e-4):
    if set(actual) != set(expected):
        raise ValueError('expected_scores must contain every model label, exactly once')
    for value in expected.values():
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not 0 <= value <= 1:
            raise ValueError('Invalid reference score')
    if abs(sum(expected.values()) - 1) > 1e-3:
        raise ValueError('Reference must be 10-class softmax probabilities, not 12 derived labels')
    delta = max(abs(actual[k] - expected[k]) for k in actual)
    return {'max_absolute_difference': delta, 'tolerance': tolerance, 'passed': delta <= tolerance}
