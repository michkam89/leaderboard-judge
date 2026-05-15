from __future__ import annotations
from judge.models import CheckResult, MUST_HAVE, ScoringConfig


def compute_scores(
    check_results: list[CheckResult],
    scoring_config: ScoringConfig | None,
) -> tuple[float, float, str | None]:
    m_total = m_pass = s_total = s_pass = 0
    for r in check_results:
        if r.check.priority == MUST_HAVE:
            m_total += 1
            if r.judgement.is_correct:
                m_pass += 1
        else:
            s_total += 1
            if r.judgement.is_correct:
                s_pass += 1

    must_have_score = m_pass / m_total * 100 if m_total else 0.0
    should_have_score = s_pass / s_total * 100 if s_total else 0.0

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
