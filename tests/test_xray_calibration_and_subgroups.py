"""Tests for X-ray subgroup (view/center/region/status) and softmax calibration analysis."""

import json
from pathlib import Path

from tools.analyze_xray_calibration_and_subgroups import (
    DEFAULT_OUTPUT,
    compute_calibration_metrics,
)


def test_compute_calibration_metrics_mathematical_invariants():
    labels = ["class_a", "class_b", "class_c"]
    y_true = ["class_a", "class_b", "class_c", "class_a"]
    probs_matrix = [
        [0.9, 0.05, 0.05],  # correct (conf 0.9)
        [0.1, 0.8, 0.1],    # correct (conf 0.8)
        [0.7, 0.2, 0.1],    # incorrect (pred class_a with conf 0.7, true class_c)
        [0.6, 0.3, 0.1],    # correct (conf 0.6)
    ]
    cal = compute_calibration_metrics(y_true, probs_matrix, labels, n_bins=10)
    assert cal["sample_count"] == 4
    assert cal["top1_accuracy"] == 0.75
    assert cal["mean_top1_confidence_all"] == 0.75
    assert cal["mean_top1_confidence_correct"] == round((0.9 + 0.8 + 0.6) / 3, 4)
    assert cal["mean_top1_confidence_incorrect"] == 0.7
    assert cal["overconfidence_gap_top1_minus_accuracy"] == 0.0
    assert 0.0 <= cal["ece_10_bin"] <= 1.0
    assert 0.0 <= cal["mce_10_bin"] <= 1.0
    assert cal["multiclass_brier_score"] > 0.0
    assert cal["negative_log_likelihood"] > 0.0
    assert sum(b["count"] for b in cal["reliability_bins"]) == 4


def test_saved_stage12_xray_subgroup_and_calibration_artifact():
    artifact_path = Path(DEFAULT_OUTPUT)
    assert artifact_path.is_file()
    data = json.loads(artifact_path.read_text(encoding="utf-8"))

    assert data["answer_ready"] is False
    assert data["independent_external_validation"] is False
    assert data["sampling"]["total_evaluated"] == 250

    cal_true = data["calibration_analysis"]["with_true_metadata"]
    cal_zero = data["calibration_analysis"]["with_zeroed_metadata_ablation"]
    assert cal_true["sample_count"] == 250
    assert cal_true["top1_accuracy"] == 0.776
    assert cal_zero["top1_accuracy"] == 0.48
    assert cal_zero["ece_10_bin"] > cal_true["ece_10_bin"]
    assert cal_zero["multiclass_brier_score"] > cal_true["multiclass_brier_score"]

    sub = data["subgroup_breakdown"]
    views = sub["by_radiographic_view"]
    assert sum(views[v]["with_true_metadata"]["sample_count"] for v in ("frontal", "lateral", "oblique")) == 250

    centers = sub["by_source_center"]
    assert sum(centers[c]["with_true_metadata"]["sample_count"] for c in centers) == 250

    statuses = sub["by_rag_mapping_status"]
    assert sum(statuses[s]["with_true_metadata"]["sample_count"] for s in statuses) == 250
