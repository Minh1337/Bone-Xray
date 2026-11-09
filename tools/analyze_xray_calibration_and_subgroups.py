"""Deterministic subgroup (center / view / anatomical region / RAG mapping status)
and softmax probability calibration analysis (ECE, MCE, Brier score, NLL, reliability bins)
for the local BTXRD checkpoint (`model/best_model.pt`) on the seed-locked 250-image
stratified sample (`per_class=25, seed=20261031`).

IMPORTANT PROVENANCE & SCOPE CONSTRAINTS:
1. As established in `tools/evaluate_xray_checkpoint.py`, `model/best_model.pt` was
   trained on BTXRD (~70% training split, `n_samples_seen_ = 2616`), and exact split
   image IDs are not stored in the checkpoint.
2. Therefore, all accuracy and calibration numbers in this artifact are IN-SOURCE
   DEVELOPMENT / ABLATION / PIPELINE-VERIFICATION metrics only (`independent_external_validation=False`,
   `answer_ready=False`).
3. This analysis fulfills the benchmark reporting specification in
   `docs/guides/README_IMAGE_REFERENCE_VI.md` (subgroup breakdown by center/view and
   calibration assessment) and empirically justifies why BoneScope labels model outputs
   as uncalibrated relative scores rather than clinical probabilities.
"""

import argparse
import json
import math
import os
import platform
import statistics
import sys
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
from rag import case_context as cases
from tools.evaluate_xray_checkpoint import (
    compute_classification_metrics,
    select_stratified_sample,
    sha256_file,
)

DEFAULT_MANIFEST = ROOT / "data" / "external_datasets" / "BTXRD" / "reference" / "manifest.csv"
DEFAULT_SOURCE_DIR = ROOT / "data" / "external_datasets" / "BTXRD" / "reference" / "source"
DEFAULT_MODEL_DIR = ROOT / "model"
DEFAULT_OUTPUT = ROOT / "docs" / "reference" / "stage12_xray_subgroup_and_calibration_20261106.json"


def compute_calibration_metrics(
    y_true: list[str],
    probs_matrix: list[list[float]],
    labels: list[str],
    n_bins: int = 10,
) -> dict:
    """Compute multi-class Brier score, NLL, 10-bin ECE, MCE, and confidence statistics."""
    label_to_idx = {label: i for i, label in enumerate(labels)}
    total = len(y_true)
    if total == 0:
        return {
            "sample_count": 0,
            "ece_10_bin": 0.0,
            "mce_10_bin": 0.0,
            "multiclass_brier_score": 0.0,
            "negative_log_likelihood": 0.0,
            "mean_top1_confidence_all": 0.0,
            "mean_top1_confidence_correct": 0.0,
            "mean_top1_confidence_incorrect": 0.0,
            "overconfidence_gap_top1_minus_accuracy": 0.0,
            "reliability_bins": [],
        }

    brier_sum = 0.0
    nll_sum = 0.0
    conf_all: list[float] = []
    conf_correct: list[float] = []
    conf_incorrect: list[float] = []
    correct_flags: list[int] = []

    for truth, probs in zip(y_true, probs_matrix):
        true_idx = label_to_idx[truth]
        # Multi-class Brier score: sum_k (p_k - y_k)^2
        brier_row = 0.0
        for k, p in enumerate(probs):
            target = 1.0 if k == true_idx else 0.0
            brier_row += (p - target) ** 2
        brier_sum += brier_row

        p_true = max(float(probs[true_idx]), 1e-12)
        nll_sum += -math.log(p_true)

        pred_idx = int(np.argmax(probs))
        top1_conf = float(probs[pred_idx])
        is_correct = 1 if pred_idx == true_idx else 0
        conf_all.append(top1_conf)
        correct_flags.append(is_correct)
        if is_correct:
            conf_correct.append(top1_conf)
        else:
            conf_incorrect.append(top1_conf)

    ece = 0.0
    mce = 0.0
    bins_report = []
    for b in range(n_bins):
        low = b / n_bins
        high = (b + 1) / n_bins
        indices = [
            i
            for i, c in enumerate(conf_all)
            if (low <= c <= high if b == 0 else low < c <= high)
        ]
        count = len(indices)
        if count > 0:
            avg_conf = sum(conf_all[i] for i in indices) / count
            avg_acc = sum(correct_flags[i] for i in indices) / count
            gap = abs(avg_conf - avg_acc)
            ece += (count / total) * gap
            if gap > mce:
                mce = gap
        else:
            avg_conf = 0.0
            avg_acc = 0.0
            gap = 0.0
        bins_report.append({
            "bin_index": b + 1,
            "range": f"[{low:.1f}, {high:.1f}]" if b == 0 else f"({low:.1f}, {high:.1f}]",
            "count": count,
            "mean_confidence": round(avg_conf, 4),
            "empirical_accuracy": round(avg_acc, 4),
            "abs_calibration_gap": round(gap, 4),
        })

    overall_acc = sum(correct_flags) / total
    mean_conf = sum(conf_all) / total
    return {
        "sample_count": total,
        "top1_accuracy": round(overall_acc, 4),
        "mean_top1_confidence_all": round(mean_conf, 4),
        "mean_top1_confidence_correct": round(statistics.mean(conf_correct), 4) if conf_correct else 0.0,
        "mean_top1_confidence_incorrect": round(statistics.mean(conf_incorrect), 4) if conf_incorrect else 0.0,
        "overconfidence_gap_top1_minus_accuracy": round(mean_conf - overall_acc, 4),
        "ece_10_bin": round(ece, 4),
        "mce_10_bin": round(mce, 4),
        "multiclass_brier_score": round(brier_sum / total, 4),
        "negative_log_likelihood": round(nll_sum / total, 4),
        "reliability_bins": bins_report,
    }


def summarize_subgroup(
    records: list[dict],
    labels: list[str],
    mode_prefix: str = "true",
) -> dict:
    """Compute Top-1, Top-3, mean confidence, and ECE for a subset of evaluation records."""
    n = len(records)
    if n == 0:
        return {"sample_count": 0}
    y_true = [r["ground_truth"] for r in records]
    top1 = [r[f"{mode_prefix}_top1"] for r in records]
    top3 = [r[f"{mode_prefix}_top3"] for r in records]
    probs = [r[f"{mode_prefix}_probs"] for r in records]

    cls_metrics = compute_classification_metrics(y_true, top1, top3, labels)
    cal_metrics = compute_calibration_metrics(y_true, probs, labels)
    return {
        "sample_count": n,
        "top1_accuracy": cls_metrics["top1_accuracy"],
        "top3_accuracy": cls_metrics["top3_accuracy"],
        "weighted_f1": cls_metrics["weighted_f1"],
        "mean_top1_confidence": cal_metrics["mean_top1_confidence_all"],
        "mean_top1_confidence_correct": cal_metrics["mean_top1_confidence_correct"],
        "mean_top1_confidence_incorrect": cal_metrics["mean_top1_confidence_incorrect"],
        "ece_10_bin": cal_metrics["ece_10_bin"],
        "multiclass_brier_score": cal_metrics["multiclass_brier_score"],
    }


@torch.inference_mode()
def run_subgroup_and_calibration_evaluation(
    manifest_path: Path = DEFAULT_MANIFEST,
    source_dir: Path = DEFAULT_SOURCE_DIR,
    model_dir: Path = DEFAULT_MODEL_DIR,
    per_class: int = 25,
    seed: int = 20261031,
    device_choice: str = "auto",
) -> dict:
    torch.set_num_threads(4)
    torch.backends.cudnn.benchmark = False
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False

    device = ("cuda" if torch.cuda.is_available() else "cpu") if device_choice == "auto" else device_choice
    predictor = Predictor(model_dir, device=device)
    labels = list(predictor.labels)

    df = pd.read_csv(manifest_path)
    sample = select_stratified_sample(df, per_class, seed)

    records: list[dict] = []
    for _, row in sample.iterrows():
        img_path = source_dir / row["relative_path"]
        meta = json.loads(row["metadata_json"])
        with Image.open(img_path) as im:
            image = np.array(im.convert("RGB"))
        x = predictor.transform(image=image)["image"].unsqueeze(0).to(predictor.device)
        meta_np = predictor.processor.transform(pd.DataFrame([meta]))
        meta_true = torch.from_numpy(meta_np).to(predictor.device)
        meta_zero = torch.zeros_like(meta_true)

        probs_true = predictor.model(x, meta_true)["flat"].softmax(1)[0].cpu().tolist()
        probs_zero = predictor.model(x, meta_zero)["flat"].softmax(1)[0].cpu().tolist()

        ranked_true = sorted(zip(labels, probs_true), key=lambda item: item[1], reverse=True)
        ranked_zero = sorted(zip(labels, probs_zero), key=lambda item: item[1], reverse=True)

        truth = str(row["ground_truth"]).strip()
        views_active = [v for v in cases.VIEW_FIELDS if int(meta.get(v, 0)) == 1]
        view_name = views_active[0] if len(views_active) == 1 else "+".join(views_active) or "none"

        regions_active = [
            reg for reg in ("lower limb", "upper limb", "pelvis") if int(meta.get(reg, 0)) == 1
        ]
        region_name = "+".join(regions_active) if regions_active else "other_site"

        records.append({
            "image_id": row["image_id"],
            "ground_truth": truth,
            "mapping_status": cases.LABEL_GUIDE[truth]["status"],
            "source_center": str(row.get("source_center") or "unknown").strip(),
            "view": view_name,
            "anatomical_region": region_name,
            "gender": str(meta.get("gender", "")).upper(),
            "true_probs": probs_true,
            "true_top1": ranked_true[0][0],
            "true_top3": [k for k, _ in ranked_true[:3]],
            "zero_probs": probs_zero,
            "zero_top1": ranked_zero[0][0],
            "zero_top3": [k for k, _ in ranked_zero[:3]],
        })

    y_true = [r["ground_truth"] for r in records]
    true_probs_all = [r["true_probs"] for r in records]
    zero_probs_all = [r["zero_probs"] for r in records]

    calibration_with_true_meta = compute_calibration_metrics(y_true, true_probs_all, labels)
    calibration_with_zero_meta = compute_calibration_metrics(y_true, zero_probs_all, labels)

    by_view = {}
    for view in ("frontal", "lateral", "oblique"):
        sub = [r for r in records if r["view"] == view]
        by_view[view] = {
            "with_true_metadata": summarize_subgroup(sub, labels, "true"),
            "with_zeroed_metadata": summarize_subgroup(sub, labels, "zero"),
        }

    by_center = {}
    for center in sorted({r["source_center"] for r in records}):
        sub = [r for r in records if r["source_center"] == center]
        by_center[f"center_{center}"] = {
            "with_true_metadata": summarize_subgroup(sub, labels, "true"),
            "with_zeroed_metadata": summarize_subgroup(sub, labels, "zero"),
        }

    by_region = {}
    for region in sorted({r["anatomical_region"] for r in records}):
        sub = [r for r in records if r["anatomical_region"] == region]
        by_region[region] = {
            "with_true_metadata": summarize_subgroup(sub, labels, "true"),
            "with_zeroed_metadata": summarize_subgroup(sub, labels, "zero"),
        }

    by_mapping_status = {}
    for status in ("direct", "unresolved", "aggregate", "no_tumor"):
        sub = [r for r in records if r["mapping_status"] == status]
        by_mapping_status[status] = {
            "with_true_metadata": summarize_subgroup(sub, labels, "true"),
            "with_zeroed_metadata": summarize_subgroup(sub, labels, "zero"),
        }

    return {
        "record_id": "stage12-xray-subgroup-and-calibration-20261106",
        "schema_version": "stage12_xray_subgroup_and_calibration_v1",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "evaluation_scope": "in_source_development_subgroup_and_calibration_analysis",
        "independent_external_validation": False,
        "answer_ready": False,
        "warnings": [
            "BTXRD is declared in model/config.json as the training dataset of best_model.pt (~70% training split, n_samples_seen_=2616).",
            "All subgroup accuracies and calibration scores (ECE, MCE, Brier, NLL) are in-source development metrics and MUST NOT be reported as independent clinical validation.",
            "Softmax scores exhibit non-zero calibration error and significant sensitivity to the 22-field metadata vector; BoneScope therefore displays them only as uncalibrated relative scores.",
        ],
        "environment": {
            "python": sys.version.split()[0],
            "platform": platform.platform(),
            "device": device,
            "gpu": torch.cuda.get_device_name(0) if device == "cuda" and torch.cuda.is_available() else None,
            "torch": torch.__version__,
        },
        "sampling": {
            "per_class_cap": per_class,
            "seed": seed,
            "total_evaluated": len(records),
            "manifest_sha256": sha256_file(manifest_path),
            "best_model_sha256": sha256_file(model_dir / "best_model.pt"),
        },
        "calibration_analysis": {
            "with_true_metadata": calibration_with_true_meta,
            "with_zeroed_metadata_ablation": calibration_with_zero_meta,
        },
        "subgroup_breakdown": {
            "by_radiographic_view": by_view,
            "by_source_center": by_center,
            "by_anatomical_region": by_region,
            "by_rag_mapping_status": by_mapping_status,
        },
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--source-dir", type=Path, default=DEFAULT_SOURCE_DIR)
    parser.add_argument("--model-dir", type=Path, default=DEFAULT_MODEL_DIR)
    parser.add_argument("--per-class", type=int, default=25)
    parser.add_argument("--seed", type=int, default=20261031)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    report = run_subgroup_and_calibration_evaluation(
        manifest_path=args.manifest,
        source_dir=args.source_dir,
        model_dir=args.model_dir,
        per_class=args.per_class,
        seed=args.seed,
        device_choice=args.device,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    cal_true = report["calibration_analysis"]["with_true_metadata"]
    cal_zero = report["calibration_analysis"]["with_zeroed_metadata_ablation"]
    print(json.dumps({
        "status": "OK",
        "output": str(args.output),
        "sample_count": report["sampling"]["total_evaluated"],
        "with_true_metadata": {
            "top1_accuracy": cal_true["top1_accuracy"],
            "mean_top1_confidence": cal_true["mean_top1_confidence_all"],
            "ece_10_bin": cal_true["ece_10_bin"],
            "brier": cal_true["multiclass_brier_score"],
        },
        "with_zeroed_metadata": {
            "top1_accuracy": cal_zero["top1_accuracy"],
            "mean_top1_confidence": cal_zero["mean_top1_confidence_all"],
            "ece_10_bin": cal_zero["ece_10_bin"],
            "brier": cal_zero["multiclass_brier_score"],
        },
    }, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
