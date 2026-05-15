from __future__ import annotations
from pathlib import Path
from typing import IO, Callable

from judge.card import load_card
from judge.client import JudgeClient
from judge.models import (
    CheckDefinition,
    CheckResult,
    EvaluationResult,
    Judgement,
    ScoringConfig,
)
from judge.scoring import compute_scores

_SYSTEM_PROMPT = """\
You are a strict, impartial evaluator.
<rules>
  1. Write your reasoning first, citing exact phrases from the conversation.
  2. Then set is_correct: true only if the criterion is fully met.
  3. Ignore filler and politeness — judge substance only.
  4. If the criterion cannot be verified from the conversation, set is_correct: false.
</rules>"""


class Judge:
    def __init__(
        self,
        api_key: str,
        base_url: str,
        model: str,
        max_retries: int = 2,
    ) -> None:
        self._client = JudgeClient(api_key=api_key, base_url=base_url, model=model)
        self._max_retries = max_retries

    def evaluate(
        self,
        conversation: list[dict],
        leaderboard_card: str | Path | IO,
        scoring_config: ScoringConfig | None = None,
        on_progress: Callable[[int, int], None] | None = None,
    ) -> EvaluationResult:
        checks = load_card(leaderboard_card)
        total = len(checks)
        transcript = "\n".join(
            f"**{turn['role'].upper()}**: {turn['content']}"
            for turn in conversation
        )
        check_results: list[CheckResult] = []

        for i, check in enumerate(checks):
            judgement = self._evaluate_check(transcript, check)
            check_results.append(CheckResult(check=check, judgement=judgement))
            if on_progress:
                on_progress(i + 1, total)

        must_have_score, should_have_score, badge = compute_scores(check_results, scoring_config)

        return EvaluationResult(
            check_results=check_results,
            must_have_score=must_have_score,
            should_have_score=should_have_score,
            badge=badge,
        )

    def _evaluate_check(
        self,
        transcript: str,
        check: CheckDefinition,
    ) -> Judgement:
        messages = [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": self._build_user_message(transcript, check)},
        ]
        for attempt in range(self._max_retries + 1):
            try:
                return self._client.judge(messages=messages, response_model=Judgement)
            except Exception:
                if attempt == self._max_retries:
                    return Judgement(
                        reasoning="evaluation failed after retries",
                        is_correct=False,
                    )

    @staticmethod
    def _build_user_message(transcript: str, check: CheckDefinition) -> str:
        pos = "\n".join(f"- {e}" for e in check.positive_examples) or "(none provided)"
        neg = "\n".join(f"- {e}" for e in check.negative_examples) or "(none provided)"
        return (
            f"<conversation>\n{transcript}\n</conversation>\n\n"
            f"<criterion>{check.criterion}</criterion>\n\n"
            f"<verification>{check.verification}</verification>\n\n"
            f"<positive_examples>\n{pos}\n</positive_examples>\n\n"
            f"<negative_examples>\n{neg}\n</negative_examples>"
        )
