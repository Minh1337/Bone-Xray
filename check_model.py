"""Local-only inference check. No training, API calls or checkpoint writes."""
import argparse
import csv
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import statistics
import sys
import time
import traceback
from datetime import datetime
from validation import META_COLS, validate_case, compare_scores

ROOT = Path(__file__).resolve().parent
os.environ.setdefault('NO_ALBUMENTATIONS_UPDATE', '1')
os.environ.setdefault('HF_HUB_OFFLINE', '1')

def sha256(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--device', choices=['auto', 'cpu', 'cuda'], default='auto')
    parser.add_argument('--cases', type=Path, default=ROOT / 'cases.json')
    parser.add_argument('--model-dir', type=Path, default=ROOT / 'model')
    parser.add_argument('--repeats', type=int, default=3)
    args = parser.parse_args()
    output = ROOT / 'results' / datetime.now().strftime('%Y%m%d_%H%M%S_%f')
    output.mkdir(parents=True)
    report = {'status': 'FAILED', 'environment': {'python': sys.version, 'os': platform.platform()},
              'cases': [], 'notes': ['Technical check only; repeatability is not notebook parity or clinical validation.']}
    log = []
    def say(message):
        print(message, flush=True)
        log.append(str(message))
    exit_code = 1
    try:
        if not 1 <= args.repeats <= 20:
            raise ValueError('repeats must be 1..20')
        packages = ['torch', 'torchvision', 'timm', 'numpy', 'pandas', 'scikit-learn', 'joblib', 'albumentations', 'opencv-python-headless', 'Pillow']
        report['environment']['packages'] = {p: importlib.metadata.version(p) for p in packages}
        import numpy as np
        import torch
        from PIL import Image
        from inference import Predictor
        torch.set_num_threads(4)
        torch.backends.cudnn.benchmark = False
        torch.backends.cuda.matmul.allow_tf32 = False
        torch.backends.cudnn.allow_tf32 = False
        import psutil
        report['environment']['ram_total_gb'] = round(psutil.virtual_memory().total / 1024**3, 2)
        report['environment']['ram_available_gb'] = round(psutil.virtual_memory().available / 1024**3, 2)
        cuda = torch.cuda.is_available()
        report['environment'].update(cuda_available=cuda, torch_cuda=torch.version.cuda)
        if args.device == 'cuda' and not cuda:
            raise RuntimeError('CUDA not available. Check NVIDIA driver, setup log, or use 03_run_cpu.bat.')
        device = 'cuda' if args.device == 'auto' and cuda else ('cpu' if args.device == 'auto' else args.device)
        report['device'] = device
        if cuda:
            prop = torch.cuda.get_device_properties(0)
            report['environment'].update(gpu=prop.name, vram_gb=round(prop.total_memory / 1024**3, 2))
        say(f'Device: {device}. Running one image at a time, FP32.')
        if device == 'cpu' and args.device == 'auto':
            say('CUDA unavailable: using CPU. Timing may be slower.')
        files = ['best_model.pt', 'metadata_processor.joblib', 'val_transform.json', 'config.json']
        missing = [f for f in files if not (args.model_dir / f).is_file()]
        if missing:
            raise FileNotFoundError(f'Missing files in model folder: {missing}')
        report['sha256'] = {f: sha256(args.model_dir / f) for f in files}
        report['sha256'].update({f: sha256(ROOT / f) for f in ['model_definition.py', 'inference.py']})
        cases = json.loads(args.cases.read_text(encoding='utf-8-sig'))
        if not isinstance(cases, list) or not cases:
            raise ValueError('cases.json must be a non-empty list')
        ids = set()
        prepared = []
        for case in cases:
            path, meta = validate_case(case, args.cases.resolve().parent)
            if case['id'] in ids:
                raise ValueError('Duplicate case id: ' + case['id'])
            ids.add(case['id'])
            with Image.open(path) as im:
                if im.width * im.height > 25_000_000:
                    raise ValueError('Image exceeds 25 million pixels')
                if getattr(im, 'n_frames', 1) != 1:
                    raise ValueError('Use a single-frame image')
                im.verify()
            prepared.append((case, path, meta))
        say('Loading trusted local checkpoint...')
        started = time.perf_counter()
        predictor = Predictor(args.model_dir, device=device)
        report['load_seconds'] = time.perf_counter() - started
        if predictor.processor.meta_cols != META_COLS or predictor.processor.feature_dim != 22:
            raise ValueError('Unexpected metadata schema/dimension')
        if len(predictor.labels) != 10 or len(set(predictor.labels)) != 10:
            raise ValueError('Expected 10 distinct class labels')
        report['labels'] = list(predictor.labels)
        # Check that the supplied config agrees with the config actually used by the model.
        import model_definition as definition
        supplied = json.loads((args.model_dir / 'config.json').read_text(encoding='utf-8-sig'))
        mismatches = {k: {'file': v, 'loaded': getattr(definition.CFG, k, None)}
                      for k, v in supplied.items() if k != 'pretrained' and getattr(definition.CFG, k, None) != v}
        report['config_mismatches'] = mismatches
        if mismatches:
            raise ValueError('config.json does not match the checkpoint; see report')
        def sync():
            if device == 'cuda':
                torch.cuda.synchronize()
        def predict(path, meta):
            sync()
            started = time.perf_counter()
            values = predictor.predict(path, meta)
            sync()
            elapsed = time.perf_counter() - started
            scores = {item['label']: float(item['score']) for item in values}
            if not all(np.isfinite(v) and 0 <= v <= 1 for v in scores.values()) or abs(sum(scores.values()) - 1) > 1e-4:
                raise ValueError('Invalid model probabilities')
            return scores, elapsed
        for case, path, meta in prepared:
            row = {'id': case['id'], 'image_name': path.name, 'image_sha256': sha256(path)}
            report['cases'].append(row)
            try:
                for key in ('true_label', 'expected_top1'):
                    if case.get(key) is not None and case[key] not in predictor.labels:
                        raise ValueError(f'Unknown {key}: {case[key]}')
                if device == 'cuda':
                    torch.cuda.reset_peak_memory_stats()
                first, warmup = predict(path, meta)
                times, deltas = [], []
                for _ in range(args.repeats):
                    current, elapsed = predict(path, meta)
                    times.append(elapsed)
                    deltas.append(max(abs(first[k] - current[k]) for k in first))
                top = sorted(first, key=first.get, reverse=True)
                row.update(scores=first, top1=top[0], top3=[{'label': k, 'score': first[k]} for k in top[:3]],
                           warmup_seconds=warmup, measured_seconds=times, median_seconds=statistics.median(times),
                           repeat_max_delta=max(deltas), repeat_pass=max(deltas) <= 1e-5,
                           notebook_comparison='NOT_PROVIDED')
                if device == 'cuda':
                    row['peak_allocated_vram_mb'] = torch.cuda.max_memory_allocated() / 1024**2
                row['process_ram_mb'] = psutil.Process().memory_info().rss / 1024**2
                if case.get('true_label') is not None:
                    row.update(true_label=case['true_label'], correct=top[0] == case['true_label'])
                if case.get('expected_top1') is not None:
                    row['expected_top1_match'] = top[0] == case['expected_top1']
                    row['notebook_comparison'] = 'TOP1_ONLY'
                if case.get('expected_scores') is not None:
                    row['score_comparison'] = compare_scores(first, case['expected_scores'])
                    row['notebook_comparison'] = 'SCORES_CHECKED'
                row['status'] = 'PASS' if row['repeat_pass'] and row.get('expected_top1_match', True) and row.get('score_comparison', {}).get('passed', True) else 'REVIEW_REQUIRED'
                say(f"{case['id']}: {top[0]} | {first[top[0]]:.4f} | median {row['median_seconds']:.3f}s | {row['status']}")
            except Exception:
                row.update(status='FAILED', error=traceback.format_exc())
                say(f"{case['id']}: FAILED (see report.json)")
                if device == 'cuda':
                    torch.cuda.empty_cache()
        report['status'] = 'TECHNICAL_CHECK_PASSED' if all(r.get('status') == 'PASS' for r in report['cases']) else 'REVIEW_REQUIRED'
        exit_code = 0 if report['status'] == 'TECHNICAL_CHECK_PASSED' else 1
        with (output / 'predictions.csv').open('w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=['id', 'status', 'top1', 'median_seconds', 'true_label', 'correct', 'notebook_comparison'], extrasaction='ignore')
            writer.writeheader()
            writer.writerows(report['cases'])
    except Exception:
        report['error'] = traceback.format_exc()
        say(report['error'])
    finally:
        (output / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
        say(f"Status: {report['status']}. Results: {output}")
        (output / 'run_log.txt').write_text('\n'.join(log), encoding='utf-8')
    return exit_code

if __name__ == '__main__':
    sys.exit(main())
