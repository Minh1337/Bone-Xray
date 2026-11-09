"""Tests for BTXRD catalogue descriptive analysis and duplicate-byte conflict inventory."""

import json
from pathlib import Path

from tools.analyze_btxrd_catalogue import DEFAULT_OUTPUT, analyze_manifest


def test_btxrd_catalogue_analysis_matches_manifest_and_duplicate_guards():
    report = analyze_manifest()
    assert report["answer_ready"] is False
    assert report["total_images"] == 3746
    assert report["unique_sha256_count"] == 3725

    dup = report["duplicate_sha256_Analysis"]
    assert dup["conflicting_metadata_group_count"] == 9
    assert "IMG000430.jpeg" in dup["conflicting_metadata_image_ids"]

    cov = report["label_guide_coverage"]
    by_status = cov["by_status"]
    total_by_status = sum(item["count"] for item in by_status.values())
    assert total_by_status == cov["mapped_single_label_count"] == 3745
    assert cov["unmapped_or_multilabel_count"] == 1
    assert total_by_status + cov["unmapped_or_multilabel_count"] == 3746
    assert report["metadata_distribution"]["demo_strict_rule_check"]["compliant_count"] == 3746
    assert report["metadata_distribution"]["source_center_counts"] == {"1": 2938, "2": 549, "3": 259}
    assert sum(report["metadata_distribution"]["radiographic_view_positive_counts"].values()) == 3746
    assert by_status["direct"]["count"] > 0
    assert by_status["unresolved"]["count"] > 0
    assert by_status["aggregate"]["count"] > 0
    assert by_status["no_tumor"]["count"] > 0

    if Path(DEFAULT_OUTPUT).is_file():
        saved = json.loads(Path(DEFAULT_OUTPUT).read_text(encoding="utf-8"))
        assert saved["manifest_sha256"] == report["manifest_sha256"]
        assert saved["total_images"] == 3746
        assert saved["duplicate_sha256_Analysis"]["conflicting_metadata_group_count"] == 9
