"""
Usage:
    OPENAI_API_KEY=sk-... .venv/bin/python smoke_test.py
    OPENAI_API_KEY=sk-... .venv/bin/python smoke_test.py --model gpt-4o
"""
import argparse
import os
import sys
from pathlib import Path

from judge import Judge, ScoringConfig, BadgeThreshold

CARD = Path(__file__).parent / "tests" / "fixtures" / "sample_card.csv"

CONVERSATION = [
    {"role": "user", "content": "Hi, I want some coaching help."},
    {
        "role": "assistant",
        "content": (
            "Hi! I'm Alex, your coach. What brings you here today? "
            "I'm here to support you on your journey."
        ),
    },
]

SCORING_CONFIG = ScoringConfig(
    thresholds=[
        BadgeThreshold(label="💎 DIAMOND", min_must_have=100.0, min_should_have=85.0),
        BadgeThreshold(label="🥇 GOLD", min_must_have=100.0, min_should_have=70.0),
        BadgeThreshold(label="🥈 SILVER", min_must_have=80.0, min_should_have=50.0),
        BadgeThreshold(label="❌ REJECTED", min_must_have=0.0, min_should_have=0.0),
    ]
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="gpt-4o-mini")
    parser.add_argument("--base-url", default="https://api.openai.com/v1")
    args = parser.parse_args()

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY environment variable not set", file=sys.stderr)
        sys.exit(1)

    print(f"Model : {args.model}")
    print(f"Card  : {CARD}\n")

    judge = Judge(api_key=api_key, base_url=args.base_url, model=args.model)

    result = judge.evaluate(
        CONVERSATION,
        leaderboard_card=CARD,
        scoring_config=SCORING_CONFIG,
        on_progress=lambda done, total: print(f"  evaluating check {done}/{total}..."),
    )

    print()
    result.print_report()


if __name__ == "__main__":
    main()
