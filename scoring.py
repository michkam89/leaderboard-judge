from __future__ import annotations
from judge.models import CheckResult, MUST_HAVE, ScoringConfig


def _category_score(results: list[CheckResult]) -> float:
    return sum(1 for r in results if r.judgement.is_correct) / len(results) * 100 if results else 0.0


def compute_scores(
    check_results: list[CheckResult],
    scoring_config: ScoringConfig | None,
) -> tuple[float, float, str | None]:
    must_have: list[CheckResult] = []
    should_have: list[CheckResult] = []
    for r in check_results:
        if r.check.priority == MUST_HAVE:
            must_have.append(r)
        else:
            should_have.append(r)

    must_have_score = _category_score(must_have)
    should_have_score = _category_score(should_have)

    badge: str | None = None
    if scoring_config:
        for threshold in scoring_config.thresholds:
            if (
                must_have_score >= threshold.min_must_have
                and should_have_score >= threshold.min_should_have
            ):
                badge = threshold.label
                break

    return must_have_score, should_have_score, badge
