"""Local API addon: reuse the user's verified inference.py unchanged."""
import hashlib
import json
import logging
import math
import os
import secrets
from contextlib import asynccontextmanager
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Lock
from time import perf_counter
from time import monotonic
import warnings

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from PIL import Image, UnidentifiedImageError
from api_validation import META_COLS, validate_case

ROOT = Path(__file__).resolve().parent
MAX_BYTES = 30 * 1024 * 1024
MAX_PIXELS = 25_000_000
LABELS = ['no-tumor', 'osteochondroma', 'multiple osteochondromas',
          'simple bone cyst', 'giant cell tumor', 'osteofibroma',
          'synovial osteochondroma', 'other bt', 'osteosarcoma', 'other mt']
logger = logging.getLogger('uvicorn.error')

def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for part in iter(lambda: f.read(1024 * 1024), b''):
            h.update(part)
    return h.hexdigest()

def load_real():
    os.environ.setdefault('NO_ALBUMENTATIONS_UPDATE', '1')
    os.environ.setdefault('HF_HUB_OFFLINE', '1')
    import torch
    from inference import Predictor
    import model_definition as definition
    torch.set_num_threads(4)
    torch.backends.cudnn.benchmark = False
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False
    device = os.environ.get('XRAY_DEVICE', 'auto')
    if device not in ('auto', 'cpu', 'cuda'):
        raise ValueError('XRAY_DEVICE must be auto, cpu or cuda')
    if device == 'auto':
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
    if device == 'cuda' and not torch.cuda.is_available():
        raise RuntimeError('CUDA is unavailable. Set XRAY_DEVICE=cpu to test CPU.')
    folder = ROOT / 'model'
    names = ['best_model.pt', 'config.json', 'metadata_processor.joblib', 'val_transform.json']
    for name in names:
        if not (folder / name).is_file():
            raise FileNotFoundError(f'Missing model/{name}')
    predictor = Predictor(folder, device=device)
    if list(predictor.labels) != LABELS:
        raise ValueError('Unexpected checkpoint labels or label order')
    if predictor.processor.meta_cols != META_COLS or predictor.processor.feature_dim != 22:
        raise ValueError('Unexpected metadata schema')
    config = json.loads((folder / 'config.json').read_text(encoding='utf-8-sig'))
    for k, v in config.items():
        if k != 'pretrained' and getattr(definition.CFG, k, None) != v:
            raise ValueError(f'Checkpoint/config mismatch: {k}')
    fingerprints = {n: digest(folder / n) for n in names}
    fingerprints.update({n: digest(ROOT / n) for n in ['inference.py', 'model_definition.py']})
    return predictor, {'device': device, 'sha256': fingerprints, 'labels': LABELS}

def checked_image(path):
    try:
        with warnings.catch_warnings():
            warnings.simplefilter('error', Image.DecompressionBombWarning)
            with Image.open(path) as im:
                if im.format not in ('JPEG', 'PNG', 'BMP', 'TIFF'):
                    raise HTTPException(415, 'Unsupported image format')
                if im.width * im.height > MAX_PIXELS:
                    raise HTTPException(413, 'Image exceeds 25 million pixels')
                if getattr(im, 'n_frames', 1) != 1:
                    raise HTTPException(415, 'Only single-frame images are supported')
                im.verify()
            with Image.open(path) as im:
                im.load()
    except HTTPException:
        raise
    except (Image.DecompressionBombWarning, Image.DecompressionBombError):
        raise HTTPException(413, 'Image dimensions are too large')
    except (OSError, ValueError, UnidentifiedImageError):
        raise HTTPException(415, 'Invalid or damaged image')

def create_app(loader=load_real):
    guard = Lock()
    @asynccontextmanager
    async def lifespan(app):
        app.state.ready = False
        app.state.pending_predictions = {}
        app.state.pending_lock = Lock()
        predictor, info = loader()  # fail startup rather than silently serving a fake model
        app.state.predictor, app.state.info = predictor, info
        app.state.ready = True
        yield
        app.state.ready = False
        app.state.predictor = None

    app = FastAPI(title='Bone X-ray API', version='0.1.0', lifespan=lifespan,
                  description='Local coursework demo. Scores are softmax outputs and are not calibrated for clinical use.')

    @app.get('/health')
    def health():
        if not getattr(app.state, 'ready', False):
            raise HTTPException(503, 'Model is not ready')
        return {'status': 'ready', **app.state.info, 'api_version': '0.1.0'}

    @app.get('/metadata-schema')
    def schema():
        return {'required_fields': META_COLS, 'age': 'number 0..120',
                'gender': ['M', 'F'], 'binary_fields': META_COLS[2:],
                'extra_fields_allowed': False, 'labels': LABELS}

    @app.post('/predict')
    def predict(file: UploadFile = File(...), metadata: str = Form(...)):
        if not getattr(app.state, 'ready', False):
            raise HTTPException(503, 'Model is not ready')
        if not guard.acquire(blocking=False):
            raise HTTPException(429, 'Model is busy; retry after the current prediction', headers={'Retry-After': '1'})
        try:
            if len(metadata) > 8192:
                raise HTTPException(422, 'Metadata is too long')
            def reject_duplicates(pairs):
                out = {}
                for k, v in pairs:
                    if k in out:
                        raise ValueError(f'Duplicate key: {k}')
                    out[k] = v
                return out
            try:
                meta = json.loads(metadata, object_pairs_hook=reject_duplicates)
            except (ValueError, TypeError, RecursionError):
                raise HTTPException(422, 'metadata must be a JSON object without duplicate keys')
            suffix = Path(file.filename or '').suffix.lower()
            if suffix not in ('.jpg', '.jpeg', '.png', '.bmp', '.tif', '.tiff'):
                raise HTTPException(415, 'Use JPG, JPEG, PNG, BMP or TIFF')
            with TemporaryDirectory(prefix='xray_api_') as directory:
                path = Path(directory) / ('image' + suffix)
                size = 0
                image_hash = hashlib.sha256()
                with path.open('wb') as target:
                    while True:
                        part = file.file.read(1024 * 1024)
                        if not part:
                            break
                        size += len(part)
                        if size > MAX_BYTES:
                            raise HTTPException(413, 'Image exceeds 30 MiB')
                        target.write(part)
                        image_hash.update(part)
                if not size:
                    raise HTTPException(422, 'Empty image')
                try:
                    validate_case({'id': 'api', 'image': str(path), 'metadata': meta}, directory)
                except ValueError as exc:
                    raise HTTPException(422, str(exc))
                checked_image(path)
                start = perf_counter()
                try:
                    values = app.state.predictor.predict(path, meta)
                    scores = {item['label']: float(item['score']) for item in values}
                    if len(values) != 10 or set(scores) != set(LABELS) or not all(math.isfinite(x) and 0 <= x <= 1 for x in scores.values()) or abs(sum(scores.values()) - 1) > 1e-4:
                        raise ValueError('Invalid predictor output')
                except Exception:
                    logger.exception('Model prediction failed')
                    raise HTTPException(500, 'Prediction failed; inspect server log')
                seconds = perf_counter() - start
                ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
                prediction_id = secrets.token_urlsafe(32)
                # Do not persist an uploader-supplied filename: it may contain
                # patient identifiers. Keep only a generic label and validated suffix.
                record = {'image_filename': 'uploaded-image' + suffix,
                          'image_sha256': image_hash.hexdigest(), 'metadata': meta,
                          'scores': scores, 'top1': ranked[0][0],
                          'top1_score': ranked[0][1], 'prediction_seconds': seconds,
                          'model_sha256': app.state.info['sha256']['best_model.pt'],
                          'device': app.state.info['device'], 'api_version': '0.1.0'}
                with app.state.pending_lock:
                    now = monotonic()
                    app.state.pending_predictions = {
                        key: value for key, value in app.state.pending_predictions.items()
                        if now - value[0] < 600
                    }
                    if len(app.state.pending_predictions) >= 1000:
                        oldest = min(app.state.pending_predictions,
                                     key=lambda key: app.state.pending_predictions[key][0])
                        del app.state.pending_predictions[oldest]
                    app.state.pending_predictions[prediction_id] = (now, record)
                return {'top1': ranked[0][0], 'top3': [{'label': k, 'score': v} for k, v in ranked[:3]],
                        'scores': scores, 'prediction_seconds': seconds, 'image_sha256': image_hash.hexdigest(),
                        'model_sha256': app.state.info['sha256']['best_model.pt'],
                        'device': app.state.info['device'], 'api_version': '0.1.0',
                        'prediction_id': prediction_id,
                        'notice': ('For coursework and research only; not for diagnosis, screening, triage, or treatment decisions. '
                                   'Scores are normalized softmax outputs, are not calibrated for clinical use, and must not be interpreted as disease probabilities.')}
        finally:
            file.file.close()
            guard.release()
    return app

app = create_app()
