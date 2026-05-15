import pytest
from judge.models import (
    CheckDefinition,
    Judgement,
    CheckResult,
    BadgeThreshold,
    ScoringConfig,
)
from judge.scoring import compute_scores


def _make_result(priority: str, is_correct: bool) -> CheckResult:
    check = CheckDefinition(
        id="X-001",
        category="Test",
        priority=priority,
        criterion="Some criterion",
        verification="Check something",
        positive_examples=[],
        negative_examples=[],
    )
    judgement = Judgement(reasoning="test", is_correct=is_correct)
    return CheckResult(check=check, judgement=judgement)


def test_all_must_have_pass():
    results = [_make_result("MUST-HAVE", True), _make_result("MUST-HAVE", True)]
    must, should, badge = compute_scores(results, None)
    assert must == 100.0
    assert should == 0.0
    assert badge is None


def test_partial_must_have_pass():
    results = [_make_result("MUST-HAVE", True), _make_result("MUST-HAVE", False)]
    must, should, badge = compute_scores(results, None)
    assert must == 50.0


def test_should_have_scoring():
    results = [
        _make_result("SHOULD-HAVE", True),
        _make_result("SHOULD-HAVE", True),
        _make_result("SHOULD-HAVE", False),
    ]
    must, should, badge = compute_scores(results, None)
    assert must == 0.0
    assert round(should, 1) == 66.7


def test_zero_must_have_checks_returns_zero():
    results = [_make_result("SHOULD-HAVE", True)]
    must, should, badge = compute_scores(results, None)
    assert must == 0.0


def test_zero_should_have_checks_returns_zero():
    results = [_make_result("MUST-HAVE", True)]
    must, should, badge = compute_scores(results, None)
    assert should == 0.0


def test_badge_first_match_wins():
    config = ScoringConfig(thresholds=[
        BadgeThreshold(label="DIAMOND", min_must_have=100.0, min_should_have=85.0),
        BadgeThreshold(label="GOLD", min_must_have=100.0, min_should_have=70.0),
        BadgeThreshold(label="SILVER", min_must_have=100.0, min_should_have=50.0),
        BadgeThreshold(label="REJECTED", min_must_have=0.0, min_should_have=0.0),
    ])
    results = [
        _make_result("MUST-HAVE", True),
        _make_result("SHOULD-HAVE", True),
        _make_result("SHOULD-HAVE", True),
        _make_result("SHOULD-HAVE", False),  # 66.7% should-have → SILVER
    ]
    must, should, badge = compute_scores(results, config)
    assert badge == "SILVER"


def test_badge_diamond():
    config = ScoringConfig(thresholds=[
        BadgeThreshold(label="DIAMOND", min_must_have=100.0, min_should_have=85.0),
        BadgeThreshold(label="GOLD", min_must_have=100.0, min_should_have=70.0),
    ])
    results = [
        _make_result("MUST-HAVE", True),
        _make_result("SHOULD-HAVE", True),
    ]
    must, should, badge = compute_scores(results, config)
    assert badge == "DIAMOND"


def test_badge_none_when_no_config():
    results = [_make_result("MUST-HAVE", True)]
    _, _, badge = compute_scores(results, None)
    assert badge is None


def test_badge_none_when_no_threshold_matches():
    config = ScoringConfig(thresholds=[
        BadgeThreshold(label="DIAMOND", min_must_have=100.0, min_should_have=100.0),
    ])
    results = [
        _make_result("MUST-HAVE", True),
        _make_result("SHOULD-HAVE", False),
    ]
    _, _, badge = compute_scores(results, config)
    assert badge is None
