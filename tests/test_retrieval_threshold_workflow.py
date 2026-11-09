"""Synthetic statistical/contract tests, never reviewer labels or real validation."""
import copy
import json
import math

import pytest

from tools import calibrate_retrieval_threshold as tool


def row(identifier, score, answerability="answerable", split="calibration", status=None):
    return {"id": identifier, "cluster_id": identifier, "question_vi": "Question " + identifier,
            "answerability": answerability, "split": split,
            "expected_status": status or ("candidates_found" if answerability == "answerable" else "insufficient_evidence"),
            "dense_top1_score": score}


CRITERIA = {"min_fully_answerable_retention": 1, "max_unsupported_candidate_rate": 0}


def test_threshold_uses_calibration_only_and_reports_holdout_failure():
    rows = [row("p", .8), row("n", .5, "unanswerable"),
            row("hp", .4, split="holdout"), row("hn", .95, "unanswerable", "holdout")]
    result = tool.analyze(rows, CRITERIA)
    assert result["candidate_threshold"] == .8
    assert result["calibration_metrics"]["tp"] == 1
    assert result["holdout_metrics"]["fn"] == 1
    assert result["holdout_metrics"]["fp"] == 1
    assert result["holdout_criteria_met"] is False
    assert result["status"] == "CANDIDATE_REQUIRES_REVIEW"
    changed = copy.deepcopy(rows)
    changed[2]["dense_top1_score"] = .99
    changed[3]["dense_top1_score"] = .1
    assert tool.analyze(changed, CRITERIA)["candidate_threshold"] == .8


def test_equal_scores_cannot_be_separated_by_a_threshold():
    result = tool.analyze([row("p", .8), row("n", .8, "unanswerable")], CRITERIA)
    assert result["status"] == "NO_FEASIBLE_THRESHOLD"
    assert result["candidate_threshold"] is None


def test_partial_is_reported_separately_and_out_of_scope_excluded_from_selection():
    result = tool.analyze([row("p", .8), row("partial", .7, "partially_answerable"),
                           row("oos", .99, "unanswerable", status="out_of_scope")], CRITERIA)
    assert result["candidate_threshold"] == .8
    assert result["calibration_metrics"]["tn"] == 1
    assert result["calibration_metrics"]["populations"]["out_of_scope"]["above_threshold"] == 1
    assert result["status"] == "CALIBRATION_ONLY"


@pytest.mark.parametrize("value", [float("nan"), float("inf"), True, None, 1.2])
def test_nonfinite_or_invalid_scores_fail(value):
    with pytest.raises(ValueError):
        tool.analyze([row("p", value)], CRITERIA)


@pytest.mark.parametrize("mutation", ["binding", "cluster", "text", "label", "criteria", "no_calibration"])
def test_bad_freeze_leakage_and_labels_are_rejected(mutation):
    dataset = tool.template()
    dataset["questions"] = [row("a", .8), row("b", .5, "unanswerable", "holdout")]
    if mutation == "binding":
        dataset["bindings"]["config"] = "tampered"
    elif mutation == "cluster":
        dataset["questions"][1]["cluster_id"] = "a"
    elif mutation == "text":
        dataset["questions"][1]["question_vi"] = " question   A "
    elif mutation == "label":
        dataset["questions"][0]["expected_status"] = "insufficient_evidence"
    elif mutation == "no_calibration":
        dataset["questions"][0]["split"] = "holdout"
    else:
        dataset["criteria"] = {**CRITERIA, "min_fully_answerable_retention": math.nan}
    with pytest.raises(ValueError):
        tool.validate_dataset(dataset, tool.bindings())


def test_blank_template_stays_pending_without_loading_embedding(tmp_path):
    path = tmp_path / "dataset.json"
    tool.write_new(path, tool.template())
    result = tool.run(path)
    assert result["status"] == "AWAITING_LABELS"
    assert result["candidate_threshold"] is None
    assert result["runtime_policy_changed"] is False
    assert result["answer_ready"] is False
    with pytest.raises(FileExistsError):
        tool.write_new(path, {})


def test_no_holdout_scoring_before_criteria_are_supplied(tmp_path):
    dataset = tool.template()
    dataset["questions"] = [row("p", .8), row("n", .5, "unanswerable"), row("h", .99, split="holdout")]
    path = tmp_path / "dataset.json"
    path.write_text(json.dumps(dataset), encoding="utf-8")
    class Engine:
        def __init__(self):
            self.seen = []
        def search(self, question, **kwargs):
            self.seen.append(question)
            return [{"score": .8 if question.endswith("p") else .5}]
    engine = Engine()
    result = tool.run(path, engine=engine)
    assert result["status"] == "AWAITING_CRITERIA"
    assert result["holdout_scored"] is False and result["withheld_holdout_count"] == 1
    assert engine.seen == ["Question p", "Question n"]
