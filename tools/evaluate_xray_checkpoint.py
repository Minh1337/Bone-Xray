"""Evaluate the local BTXRD checkpoint on a deterministic reference sample or full manifest.

IMPORTANT LIMITATIONS (recorded in every output artifact):
1. The current checkpoint (`model/best_model.pt`) declares BTXRD in its training
   configuration (`config.json`), and only a `split_signature` hash was saved—not
   the exact train/validation/test image ID list.
2. Furthermore, `metadata_processor.joblib` records `n_samples_seen_ = 2616`
   (~69.8% of the 3,746 BTXRD rows), confirming that ~70% of BTXRD was used to fit
   the training split.
3. Therefore, every BTXRD row has `partition=unassigned` and
   `independent_of_checkpoint_training=false`. Metrics produced by this tool are
   IN-SOURCE / DEVELOPMENT / PIPELINE-VERIFICATION metrics only and MUST NOT be
   presented as independent external test accuracy or clinical performance.

What this tool provides for the educational report (P2 & P5):
- Deterministic, seed-locked stratified sampling from `manifest.csv` (or full-manifest evaluation).
- Full 10-class confusion matrix, per-class precision/recall/F1/support, macro-F1,
  weighted-F1, Top-1 and Top-3 accuracy, and inference latency distribution.
- Controlled ablation on the exact same sample comparing:
  (a) Image + true metadata (`use_metadata` normal path), vs.
  (b) Image + neutral/zeroed metadata vector (all 22 transformed features set to 0.0,
       isolating the effect of the MetadataMLP + Cross-Attention gates).
"""

import argparse
import hashlib
import json
import os
import platform
import statistics
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ.setdefault("NO_ALBUMENTATIONS_UPDATE", "1")
os.environ.setdefault("HF_HUB_OFFLINE", "1")

from inference import Predictor
import model_definition as definition


def sha256_file(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def select_stratified_sample(df, per_class, seed):
    """Deterministically sample up to `per_class` valid unique-hash rows per label."""
    valid = df[(df["ground_truth_status"] == "ok") & (df["metadata_status"] == "ok")].copy()
    valid = valid.sort_values("image_id").reset_index(drop=True)
    if per_class <= 0:
        return valid
    rng = np.random.default_rng(seed)
    chosen_Parts = []
    for label in sorted(valid["ground_truth"].unique()):
        sub = valid[valid["ground_truth"] == label]
        if len(sub) <= per_class:
            chosen_Parts.append(sub)
        else:
            idx = rng.choice(sub.index.to_numpy(), size=per_class, replace=False)
            chosen_Parts.append(sub.loc[np.sort(idx)])
    return pd.concat(chosen_Parts, ignore_index=True)


def compute_classification_metrics(y_true, y_pred_top1, y_pred_top3, labels):
    label_to_idx = {label: i for i, label in enumerate(labels)}
    n = len(labels)
    cm = [[0] * n for _ in range(n)]
    top1_hits = 0
    top3_hits = 0
    for truth, pred1, pred3 in zip(y_true, y_pred_top1, y_pred_top3):
        ti = label_to_idx[truth]
        pi = label_to_idx[pred1]
        cm[ti][pi] += 1
        if truth == pred1:
            top1_hits += 1
        if truth in pred3:
            top3_hits += 1

    per_class = {}
    f1_list = []
    weighted_f1_sum = 0.0
    total = len(y_true)
    for i, label in enumerate(labels):
        tp = cm[i][i]
        fp = sum(cm[r][i] for r in range(n) if r != i)
        fn = sum(cm[i][c] for c in range(n) if c != i)
        support = sum(cm[i])
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0
        per_class[label] = {
            "support": support,
            "tp": tp,
            "fp": fp,
            "fn": fn,
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1": round(f1, 4),
        }
        f1_list.append(f1)
        weighted_f1_sum += f1 * support

    return {
        "sample_count": total,
        "top1_accuracy": round(top1_hits / total, 4) if total else 0.0,
        "top3_accuracy": round(top3_hits / total, 4) if total else 0.0,
        "macro_f1": round(sum(f1_list) / len(f1_list), 4) if f1_list else 0.0,
        "weighted_f1": round(weighted_f1_sum / total, 4) if total else 0.0,
        "per_class": per_class,
        "confusion_matrix": {
            "labels": list(labels),
            "matrix_rows_true_cols_pred": cm,
        },
    }


@torch.inference_mode()
def predict_both_modes(predictor, image_path, metadata):
    """Run forward pass with true metadata and with neutral zeroed metadata tensor."""
    with Image.open(image_path) as im:
        image = np.array(im.convert("RGB"))
    x = predictor.transform(image=image)["image"].unsqueeze(0).to(predictor.device)
    meta_np = predictor.processor.transform(pd.DataFrame([metadata]))
    meta_true = torch.from_numpy(meta_np).to(predictor.device)
    meta_zero = torch.zeros_like(meta_true)

    if predictor.device.type == "cuda":
        torch.cuda.synchronize()
    t0 = time.perf_counter()
    probs_true = predictor.model(x, meta_true)["flat"].softmax(1)[0].cpu().tolist()
    if predictor.device.type == "cuda":
        torch.cuda.synchronize()
    elapsed = time.perf_counter() - t0

    probs_zero = predictor.model(x, meta_zero)["flat"].softmax(1)[0].cpu().tolist()
    ranked_true = sorted(zip(predictor.labels, probs_true), key=lambda item: item[1], reverse=True)
    ranked_zero = sorted(zip(predictor.labels, probs_zero), key=lambda item: item[1], reverse=True)
    return ranked_true, ranked_zero, elapsed


def inspect_checkpoint_provenance(model_dir):
    ckpt = torch.load(model_dir / "best_model.pt", map_location="cpu", weights_only=False)
    state = pd.Series(ckpt.keys()).tolist()
    import joblib
    proc = joblib.load(model_dir / "metadata_processor.joblib")
    age_info = proc["colinfo"].get("age", {})
    scaler = age_info.get("scaler")
    return {
        "checkpoint_keys": state,
        "best_epoch": ckpt.get("best_epoch"),
        "best_val_mAP_recorded_in_ckpt": round(float(ckpt.get("best_val_mAP", 0.0)), 6),
        "best_threshold_recorded_in_ckpt": ckpt.get("best_threshold"),
        "split_signature_sha256": ckpt.get("split_signature"),
        "split_ids_present_in_checkpoint": False,
        "training_csv_path_in_config": ckpt.get("config", {}).get("csv_path"),
        "group_column_in_config": ckpt.get("config", {}).get("group_column"),
        "seed_in_config": ckpt.get("config", {}).get("seed"),
        "val_ratio_in_config": ckpt.get("config", {}).get("val_ratio"),
        "test_ratio_in_config": ckpt.get("config", {}).get("test_ratio"),
        "metadata_processor_age_n_samples_seen": int(getattr(scaler, "n_samples_seen_", 0)) if scaler else None,
        "metadata_processor_age_mean": round(float(scaler.mean_[0]), 4) if scaler else None,
        "metadata_processor_age_std": round(float(scaler.scale_[0]), 4) if scaler else None,
        "metadata_processor_age_median_fill": age_info.get("fill"),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=ROOT / "data/external_datasets/BTXRD/reference/manifest.csv")
    parser.add_argument("--source-dir", type=Path, default=ROOT / "data/external_datasets/BTXRD/reference/source")
    parser.add_argument("--model-dir", type=Path, default=ROOT / "model")
    parser.add_argument("--per-class", type=int, default=25,
                        help="Number of rows per class for stratified sample (0 = full manifest).")
    parser.add_argument("--seed", type=int, default=20261031)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    parser.add_argument("--output", type=Path,
                        default=ROOT / "docs/reference/stage11_xray_in_source_evaluation_20261103.json")
    args = parser.parse_args()

    torch.set_num_threads(4)
    torch.backends.cudnn.benchmark = False
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False

    device = ("cuda" if torch.cuda.is_available() else "cpu") if args.device == "auto" else args.device
    predictor = Predictor(args.model_dir, device=device)
    labels = list(predictor.labels)

    df = pd.read_csv(args.manifest)
    sample = select_stratified_sample(df, args.per_class, args.seed)
    sample_id_digest = hashlib.sha256("\n".join(sample["image_id"].tolist()).encode("utf-8")).hexdigest()

    y_true = []
    pred_true_top1, pred_true_top3 = [], []
    pred_zero_top1, pred_zero_top3 = [], []
    latencies = []
    top1_changed_count = 0

    for _, row in sample.iterrows():
        img_path = args.source_dir / row["relative_path"]
        meta = json.loads(row["metadata_json"])
        ranked_true, ranked_zero, elapsed = predict_both_modes(predictor, img_path, meta)
        truth = row["ground_truth"]
        y_true.append(truth)
        t1_true = ranked_true[0][0]
        t1_zero = ranked_zero[0][0]
        pred_true_top1.append(t1_true)
        pred_true_top3.append([k for k, _ in ranked_true[:3]])
        pred_zero_top1.append(t1_zero)
        pred_zero_top3.append([k for k, _ in ranked_zero[:3]])
        if t1_true != t1_zero:
            top1_changed_count += 1
        latencies.append(elapsed)

    metrics_with_meta = compute_classification_metrics(y_true, pred_true_top1, pred_true_top3, labels)
    metrics_zero_meta = compute_classification_metrics(y_true, pred_zero_top1, pred_zero_top3, labels)

    record = {
        "schema_version": "stage11_xray_in_source_eval_v1",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "evaluation_scope": "in_source_development_and_ablation_only",
        "independent_external_validation": False,
        "answer_ready": False,
        "warnings": [
            "BTXRD is declared in model/config.json as the training dataset of best_model.pt.",
            "Exact train/val/test split image IDs are not stored in the checkpoint (only split_signature hash d812e544... and metadata_processor n_samples_seen_=2616).",
            "Therefore, roughly 70% of sampled BTXRD images belonged to the training split. Do NOT report these numbers as held-out test accuracy or external clinical performance.",
        ],
        "environment": {
            "python": sys.version.split()[0],
            "platform": platform.platform(),
            "device": device,
            "gpu": torch.cuda.get_device_name(0) if device == "cuda" and torch.cuda.is_available() else None,
            "torch": torch.__version__,
        },
        "fingerprints_sha256": {
            "best_model.pt": sha256_file(args.model_dir / "best_model.pt"),
            "metadata_processor.joblib": sha256_file(args.model_dir / "metadata_processor.joblib"),
            "val_transform.json": sha256_file(args.model_dir / "val_transform.json"),
            "config.json": sha256_file(args.model_dir / "config.json"),
            "model_definition.py": sha256_file(ROOT / "model_definition.py"),
            "inference.py": sha256_file(ROOT / "inference.py"),
            "btxrd_manifest_csv": sha256_file(args.manifest),
            "sampled_image_ids_sha256": sample_id_digest,
        },
        "checkpoint_provenance_audit": inspect_checkpoint_provenance(args.model_dir),
        "sampling": {
            "strategy": "stratified_by_ground_truth_sorted_by_image_id" if args.per_class > 0 else "full_valid_manifest",
            "per_class_cap": args.per_class,
            "seed": args.seed,
            "total_evaluated": len(sample),
        },
        "latency_seconds": {
            "median": round(statistics.median(latencies), 4) if latencies else 0.0,
            "mean": round(statistics.mean(latencies), 4) if latencies else 0.0,
            "p95": round(float(np.percentile(latencies, 95)), 4) if latencies else 0.0,
            "min": round(min(latencies), 4) if latencies else 0.0,
            "max": round(max(latencies), 4) if latencies else 0.0,
        },
        "results_with_true_metadata": metrics_with_meta,
        "ablation_with_zeroed_metadata": {
            "description": "Same images and checkpoint, but the 22-dim transformed metadata vector is set to all zeros before MetadataMLP + Cross-Attention.",
            "top1_predictions_changed_count": top1_changed_count,
            "top1_predictions_changed_fraction": round(top1_changed_count / len(sample), 4) if len(sample) else 0.0,
            "metrics": metrics_zero_meta,
        },
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "output": str(args.output),
        "sample_count": len(sample),
        "device": device,
        "median_latency_s": record["latency_seconds"]["median"],
        "with_metadata": {
            "top1": metrics_with_meta["top1_accuracy"],
            "top3": metrics_with_meta["top3_accuracy"],
            "macro_f1": metrics_with_meta["macro_f1"],
        },
        "zeroed_metadata_ablation": {
            "top1": metrics_zero_meta["top1_accuracy"],
            "top3": metrics_zero_meta["top3_accuracy"],
            "macro_f1": metrics_zero_meta["macro_f1"],
            "top1_changed_count": top1_changed_count,
        },
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
