import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch
from judge.judge import Judge
from judge.models import Judgement, ScoringConfig, BadgeThreshold

FIXTURE_CARD = Path(__file__).parent / "fixtures" / "sample_card.csv"

SAMPLE_CONVERSATION = [
    {"role": "user", "content": "Hi, I want some help."},
    {"role": "assistant", "content": "Hi! I'm Alex, your coach. What brings you here today?"},
]


def make_judge(mock_client=None):
    judge = Judge(api_key="test", base_url="http://test", model="test-model")
    if mock_client is not None:
        judge._client = mock_client
    return judge


def _good_judgement():
    return Judgement(reasoning="criterion met", is_correct=True)


def _bad_judgement():
    return Judgement(reasoning="criterion not met", is_correct=False)


def test_evaluate_calls_judge_once_per_check():
    mock_client = MagicMock()
    mock_client.judge.return_value = _good_judgement()

    judge = make_judge(mock_client)
    result = judge.evaluate(SAMPLE_CONVERSATION, FIXTURE_CARD)

    assert mock_client.judge.call_count == 3  # 3 non-blank rows in fixture


def test_evaluate_returns_correct_check_count():
    mock_client = MagicMock()
    mock_client.judge.return_value = _good_judgement()

    judge = make_judge(mock_client)
    result = judge.evaluate(SAMPLE_CONVERSATION, FIXTURE_CARD)

    assert len(result.check_results) == 3


def test_evaluate_scores_all_pass():
    mock_client = MagicMock()
    mock_client.judge.return_value = _good_judgement()

    judge = make_judge(mock_client)
    result = judge.evaluate(SAMPLE_CONVERSATION, FIXTURE_CARD)

    assert result.must_have_score == 100.0
    assert result.should_have_score == 100.0


def test_evaluate_scores_some_fail():
    mock_client = MagicMock()
    # LC-001 pass, LC-002 fail, LC-003 pass
    mock_client.judge.side_effect = [_good_judgement(), _bad_judgement(), _good_judgement()]

    judge = make_judge(mock_client)
    result = judge.evaluate(SAMPLE_CONVERSATION, FIXTURE_CARD)

    assert result.must_have_score == 50.0   # 1/2 MUST-HAVE passed
    assert result.should_have_score == 100.0  # 1/1 SHOULD-HAVE passed


def test_evaluate_progress_callback():
    mock_client = MagicMock()
    mock_client.judge.return_value = _good_judgement()

    calls = []
    judge = make_judge(mock_client)
    judge.evaluate(SAMPLE_CONVERSATION, FIXTURE_CARD, on_progress=lambda d, t: calls.append((d, t)))

    assert calls == [(1, 3), (2, 3), (3, 3)]


def test_evaluate_retries_on_failure_then_records_failed_judgement():
    mock_client = MagicMock()
    # First check always raises; after max_retries it records failed judgement
    mock_client.judge.side_effect = [
        Exception("LLM error"),
        Exception("LLM error"),
        Exception("LLM error"),
        _good_judgement(),  # second check passes
        _good_judgement(),  # third check passes
    ]

    judge = Judge(api_key="test", base_url="http://test", model="m", max_retries=2)
    judge._client = mock_client
    result = judge.evaluate(SAMPLE_CONVERSATION, FIXTURE_CARD)

    assert result.check_results[0].judgement.is_correct is False
    assert "failed" in result.check_results[0].judgement.reasoning
    assert result.check_results[1].judgement.is_correct is True


def test_evaluate_applies_scoring_config():
    mock_client = MagicMock()
    mock_client.judge.return_value = _good_judgement()

    config = ScoringConfig(thresholds=[
        BadgeThreshold(label="DIAMOND", min_must_have=100.0, min_should_have=85.0),
        BadgeThreshold(label="GOLD", min_must_have=100.0, min_should_have=70.0),
    ])
    judge = make_judge(mock_client)
    result = judge.evaluate(SAMPLE_CONVERSATION, FIXTURE_CARD, scoring_config=config)

    assert result.badge == "DIAMOND"


def test_evaluate_badge_none_without_config():
    mock_client = MagicMock()
    mock_client.judge.return_value = _good_judgement()

    judge = make_judge(mock_client)
    result = judge.evaluate(SAMPLE_CONVERSATION, FIXTURE_CARD)

    assert result.badge is None


def test_user_message_contains_xml_tags():
    mock_client = MagicMock()
    mock_client.judge.return_value = _good_judgement()

    judge = make_judge(mock_client)
    judge.evaluate(SAMPLE_CONVERSATION, FIXTURE_CARD)

    call_args = mock_client.judge.call_args_list[0]
    user_message = call_args.kwargs["messages"][1]["content"]
    assert "<conversation>" in user_message
    assert "<criterion>" in user_message
    assert "<verification>" in user_message
    assert "<positive_examples>" in user_message
    assert "<negative_examples>" in user_message


def test_conversation_transcript_format():
    mock_client = MagicMock()
    mock_client.judge.return_value = _good_judgement()

    judge = make_judge(mock_client)
    judge.evaluate(SAMPLE_CONVERSATION, FIXTURE_CARD)

    call_args = mock_client.judge.call_args_list[0]
    user_message = call_args.kwargs["messages"][1]["content"]
    assert "**USER**:" in user_message
    assert "**ASSISTANT**:" in user_message
