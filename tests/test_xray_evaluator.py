"""Unit tests for tools/evaluate_xray_checkpoint.py."""

import pandas as pd

from tools.evaluate_xray_checkpoint import compute_classification_metrics, select_stratified_sample


def test_compute_classification_metrics_confusion_and_f1():
    labels = ["no-tumor", "osteochondroma", "osteosarcoma"]
    y_true = ["no-tumor", "no-tumor", "osteochondroma", "osteosarcoma"]
    y_top1 = ["no-tumor", "osteochondroma", "osteochondroma", "osteosarcoma"]
    y_top3 = [
        ["no-tumor", "osteochondroma", "osteosarcoma"],
        ["osteochondroma", "no-tumor", "osteosarcoma"],
        ["osteochondroma", "no-tumor", "osteosarcoma"],
        ["osteosarcoma", "osteochondroma", "no-tumor"],
    ]
    res = compute_classification_metrics(y_true, y_top1, y_top3, labels)
    assert res["sample_count"] == 4
    assert res["top1_accuracy"] == 0.75
    assert res["top3_accuracy"] == 1.0
    assert res["confusion_matrix"]["matrix_rows_true_cols_pred"] == [
        [1, 1, 0],
        [0, 1, 0],
        [0, 0, 1],
    ]
    assert res["per_class"]["osteosarcoma"]["f1"] == 1.0


def test_select_stratified_sample_is_deterministic_and_filters_invalid():
    rows = []
    for idx in range(10):
        rows.append({
            "image_id": f"IMG_{idx:03d}.jpg",
            "ground_truth": "osteochondroma" if idx < 5 else "osteosarcoma",
            "ground_truth_status": "ok",
            "metadata_status": "ok",
        })
    rows.append({
        "image_id": "IMG_BAD.jpg",
        "ground_truth": "",
        "ground_truth_status": "multiple_subtype_labels",
        "metadata_status": "ok",
    })
    df = pd.DataFrame(rows)
    s1 = select_stratified_sample(df, per_class=3, seed=42)
    s2 = select_stratified_sample(df, per_class=3, seed=42)
    assert len(s1) == 6
    assert s1["image_id"].tolist() == s2["image_id"].tolist()
    assert "IMG_BAD.jpg" not in s1["image_id"].tolist()
