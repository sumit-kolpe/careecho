import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from careecho.metrics import classification_metrics, word_errors
from careecho.nlp import contains, review, sentences
from careecho.schema import Plan

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def plan():
    return Plan.model_validate_json((ROOT / "data/plans/wound.json").read_text())


def test_exact_evidence_offsets(plan):
    text = "  I take cephalexin twice daily for five days.\nI change the dressing daily!"
    report = review(plan, text)
    assert report.findings[0].status == "covered"
    for finding in report.findings:
        for ev in finding.evidence:
            assert text[ev.start : ev.end] == ev.quote


@pytest.mark.parametrize(
    "text, expected",
    [
        ("", "missing"),
        ("I take cephalexin.", "needs_review"),
        ("I take cephalexin twice daily for five days.", "covered"),
        ("I do not take cephalexin twice daily for five days.", "needs_review"),
        ("I don’t take cephalexin twice daily for five days.", "needs_review"),
        ("I take cephalexin once daily for five days.", "possible_conflict"),
        ("I take vitamins twice daily for five days. Cephalexin.", "needs_review"),
    ],
)
def test_medication_status(plan, text, expected):
    assert review(plan, text).findings[0].status == expected


def test_boundaries_and_decimals():
    assert not contains("dailycare", "daily")
    assert len(sentences("I take 2.5 mg. Next step.")) == 2


def test_barriers(plan):
    report = review(plan, "I can't afford this. I have no ride. I live alone.")
    assert {b.category for b in report.barriers} == {"cost", "transport", "support"}
    assert report.requires_human_review


def test_no_implicit_cloud_call(plan, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "not-a-real-key")
    assert review(plan, "").engine == "rules-v1"


def test_plan_validation(plan):
    data = plan.model_dump()
    data["targets"].append(data["targets"][0])
    with pytest.raises(ValidationError):
        Plan.model_validate(data)


def test_metric_edit_distance():
    assert word_errors("take twice daily", "take once daily") == (1, 3)
    assert word_errors("", "extra words") == (2, 0)
    assert word_errors("Take it!", "take it") == (0, 2)


def test_unsafe_coverage_metric():
    result = classification_metrics([("missing", "covered"), ("covered", "covered")])
    assert result["unsafe_coverage_count"] == 1
    assert result["accuracy"] == 0.5


def test_dataset_complete_and_offsets():
    cases = json.loads((ROOT / "data/cases.json").read_text())
    for case in cases:
        plan = Plan.model_validate_json((ROOT / f"data/plans/{case['plan']}.json").read_text())
        result = review(plan, case["transcript"])
        assert set(case["expected"]) == {f.target_id for f in result.findings}
        for finding in result.findings:
            for ev in finding.evidence:
                assert case["transcript"][ev.start : ev.end] == ev.quote
