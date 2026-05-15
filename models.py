from __future__ import annotations
from typing import Literal
from pydantic import BaseModel

MUST_HAVE = "MUST-HAVE"
SHOULD_HAVE = "SHOULD-HAVE"


class CheckDefinition(BaseModel):
    id: str
    category: str
    priority: Literal["MUST-HAVE", "SHOULD-HAVE"]
    criterion: str
    verification: str
    positive_examples: list[str]
    negative_examples: list[str]


class Judgement(BaseModel):
    reasoning: str
    is_correct: bool


class CheckResult(BaseModel):
    check: CheckDefinition
    judgement: Judgement


class BadgeThreshold(BaseModel):
    label: str
    min_must_have: float
    min_should_have: float


class ScoringConfig(BaseModel):
    thresholds: list[BadgeThreshold]


class EvaluationResult(BaseModel):
    check_results: list[CheckResult]
    must_have_score: float
    should_have_score: float
    badge: str | None

    def print_report(self) -> None:
        must_total = must_passed = should_total = should_passed = 0
        lines: list[str] = []
        for result in self.check_results:
            if result.check.priority == MUST_HAVE:
                must_total += 1
                if result.judgement.is_correct:
                    must_passed += 1
            else:
                should_total += 1
                if result.judgement.is_correct:
                    should_passed += 1
            icon = "✅" if result.judgement.is_correct else "❌"
            lines.append(f"{icon} {result.check.id}  [{result.check.category}]  {result.check.criterion}")
            if not result.judgement.is_correct:
                lines.append(f"   └─ Reasoning: {result.judgement.reasoning}")

        print("=== EVALUATION REPORT ===\n")
        print(f"MUST-HAVE:    {must_passed}/{must_total}  ({self.must_have_score:.1f}%)")
        print(f"SHOULD-HAVE:  {should_passed}/{should_total}  ({self.should_have_score:.1f}%)")
        if self.badge:
            print(f"BADGE:        {self.badge}")
        print()
        for line in lines:
            print(line)
