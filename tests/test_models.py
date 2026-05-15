import pytest
from pydantic import ValidationError
from judge.models import (
    CheckDefinition,
    Judgement,
    CheckResult,
    BadgeThreshold,
    ScoringConfig,
    EvaluationResult,
)


def make_check(**kwargs):
    defaults = dict(
        id="LC-001",
        category="Onboarding",
        priority="MUST-HAVE",
        criterion="Coach introduces itself",
        verification="Check first message",
        positive_examples=["Hi I'm Alex"],
        negative_examples=["How can I help?"],
    )
    defaults.update(kwargs)
    return CheckDefinition(**defaults)


def make_judgement(is_correct=True):
    return Judgement(reasoning="looks good", is_correct=is_correct)


def test_check_definition_valid():
    check = make_check()
    assert check.id == "LC-001"
    assert check.priority == "MUST-HAVE"


def test_check_definition_invalid_priority():
    with pytest.raises(ValidationError):
        make_check(priority="NICE-TO-HAVE")


def test_judgement_fields():
    j = Judgement(reasoning="analysis here", is_correct=False)
    assert j.is_correct is False
    assert j.reasoning == "analysis here"


def test_check_result_composes():
    check = make_check()
    judgement = make_judgement()
    result = CheckResult(check=check, judgement=judgement)
    assert result.check.id == "LC-001"
    assert result.judgement.is_correct is True


def test_badge_threshold_fields():
    bt = BadgeThreshold(label="GOLD", min_must_have=100.0, min_should_have=70.0)
    assert bt.label == "GOLD"


def test_scoring_config_holds_thresholds():
    config = ScoringConfig(thresholds=[
        BadgeThreshold(label="DIAMOND", min_must_have=100.0, min_should_have=85.0),
        BadgeThreshold(label="GOLD", min_must_have=100.0, min_should_have=70.0),
    ])
    assert len(config.thresholds) == 2


def test_evaluation_result_fields():
    check = make_check()
    judgement = make_judgement()
    result = EvaluationResult(
        check_results=[CheckResult(check=check, judgement=judgement)],
        must_have_score=100.0,
        should_have_score=0.0,
        badge="GOLD",
    )
    assert result.badge == "GOLD"
    assert result.must_have_score == 100.0


def test_evaluation_result_badge_none_when_not_provided():
    check = make_check()
    judgement = make_judgement()
    result = EvaluationResult(
        check_results=[CheckResult(check=check, judgement=judgement)],
        must_have_score=100.0,
        should_have_score=100.0,
        badge=None,
    )
    assert result.badge is None
