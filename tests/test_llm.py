from pathlib import Path
from types import SimpleNamespace

import pytest

from careecho.llm import ModelFinding, ModelReview, review_with_llm, validate_response
from careecho.schema import Plan


@pytest.fixture
def plan():
    return Plan.model_validate_json(
        (Path(__file__).resolve().parents[1] / "data/plans/therapy.json").read_text()
    )


def response(quote="I do exercises."):
    return ModelReview(
        findings=[
            ModelFinding(
                target_id="exercise", status="needs_review", quotes=[quote], reason="Timing absent."
            ),
            ModelFinding(
                target_id="followup", status="missing", quotes=[], reason="Not mentioned."
            ),
        ]
    )


def test_valid_response(plan):
    report = validate_response(plan, "I do exercises.", response(), "test-model")
    assert report.findings[0].evidence[0].start == 0
    assert report.findings[0].question == plan.targets[0].question


def test_hallucinated_quote_rejected(plan):
    with pytest.raises(ValueError, match="exact transcript"):
        validate_response(plan, "I do exercises.", response("I take insulin."), "test-model")


def test_unknown_and_duplicate_ids(plan):
    result = response()
    result.findings[1].target_id = "exercise"
    with pytest.raises(ValueError, match="target IDs"):
        validate_response(plan, "I do exercises.", result, "test-model")


@pytest.mark.parametrize("consent, synthetic", [(False, True), (True, False)])
def test_cloud_gate(plan, consent, synthetic):
    plan.synthetic = synthetic
    with pytest.raises(ValueError, match="explicit consent"):
        review_with_llm(plan, "I do exercises.", consent=consent, model="test-model")


def test_mocked_api_contract(plan):
    calls = []

    def parse(**kwargs):
        calls.append(kwargs)
        return SimpleNamespace(output_parsed=response())

    client = SimpleNamespace(responses=SimpleNamespace(parse=parse))
    result = review_with_llm(
        plan, "I do exercises.", consent=True, model="test-model", client=client
    )
    assert calls[0]["store"] is False
    assert calls[0]["text_format"] is ModelReview
    assert result.engine == "openai:test-model"


def test_refusal_rejected(plan):
    client = SimpleNamespace(
        responses=SimpleNamespace(parse=lambda **kw: SimpleNamespace(output_parsed=None))
    )
    with pytest.raises(ValueError, match="declined"):
        review_with_llm(plan, "some text", consent=True, model="test-model", client=client)
