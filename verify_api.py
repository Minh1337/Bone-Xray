"""Compare API predictions with the user's saved local run, not with notebook outputs."""
import argparse
from datetime import datetime
import hashlib
import json
from pathlib import Path
import sys
import traceback
import httpx

ROOT = Path(__file__).resolve().parent

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--url', default='http://127.0.0.1:8000')
    args = parser.parse_args()
    out = ROOT / 'api_results' / datetime.now().strftime('%Y%m%d_%H%M%S_%f')
    out.mkdir(parents=True)
    report = {'status': 'FAILED', 'comparison': 'API versus saved LOCAL run; notebook parity remains unverified', 'cases': []}
    lines = []
    try:
        baseline = json.loads((ROOT / 'api_reference_local.json').read_text(encoding='utf-8-sig'))
        cases = json.loads((ROOT / 'cases.json').read_text(encoding='utf-8-sig'))
        by_id = {c['id']: c for c in baseline['cases']}
        if len(cases) != 3 or {c['id'] for c in cases} != set(by_id):
            raise ValueError('Use the three original case IDs for this comparison')
        with httpx.Client(base_url=args.url, timeout=120, trust_env=False) as client:
            health = client.get('/health')
            health.raise_for_status()
            report['health'] = health.json()
            report['artifact_hashes_match'] = all(health.json()['sha256'].get(k) == v for k, v in baseline['sha256'].items())
            if not report['artifact_hashes_match']:
                raise ValueError('Model/code/config hashes differ from verified local run')
            for case in cases:
                row = {'id': case['id'], 'status': 'FAILED'}
                report['cases'].append(row)
                try:
                    path = ROOT / case['image']
                    reference = by_id[case['id']]
                    row['metadata_matches'] = case['metadata'] == reference['metadata']
                    if not row['metadata_matches']:
                        raise ValueError('Metadata differs from the three original reference cases')
                    row['image_hash_matches'] = hashlib.sha256(path.read_bytes()).hexdigest() == reference['image_sha256']
                    if not row['image_hash_matches']:
                        raise ValueError('Image bytes differ from local reference')
                    with path.open('rb') as f:
                        response = client.post('/predict', data={'metadata': json.dumps(case['metadata'])}, files={'file': (path.name, f)})
                    response.raise_for_status()
                    answer = response.json()
                    row['response'] = answer
                    row['max_score_delta'] = max(abs(answer['scores'][k] - v) for k, v in reference['scores'].items())
                    row['top1_matches'] = answer['top1'] == reference['top1']
                    row['tolerance'] = 1e-4
                    row['status'] = 'PASS' if row['max_score_delta'] <= row['tolerance'] and row['top1_matches'] else 'REVIEW_REQUIRED'
                except Exception:
                    row['error'] = traceback.format_exc()
                lines.append(f"{case['id']}: {row['status']}")
            # Actual HTTP rejection checks; no real model inference should run here.
            with (ROOT / cases[0]['image']).open('rb') as f:
                r = client.post('/predict', data={'metadata': '{}'}, files={'file': ('test.jpg', f)})
            report['missing_metadata_rejected'] = r.status_code == 422
            r = client.post('/predict', data={'metadata': json.dumps(cases[0]['metadata'])}, files={'file': ('bad.jpg', b'not an image')})
            report['corrupt_image_rejected'] = r.status_code == 415
        good = all(c['status'] == 'PASS' for c in report['cases']) and report['missing_metadata_rejected'] and report['corrupt_image_rejected']
        report['status'] = 'API_LOCAL_PARITY_PASSED' if good else 'REVIEW_REQUIRED'
    except Exception:
        report['error'] = traceback.format_exc()
        lines.append(report['error'])
    finally:
        lines.append(f"Status: {report['status']}\nResults: {out}")
        (out / 'api_report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
        (out / 'api_run_log.txt').write_text('\n'.join(lines), encoding='utf-8')
        print('\n'.join(lines))
    return 0 if report['status'] == 'API_LOCAL_PARITY_PASSED' else 1

if __name__ == '__main__':
    sys.exit(main())
