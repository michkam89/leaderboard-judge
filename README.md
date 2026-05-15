# leaderboard-judge

An LLM-as-a-Judge evaluation library that scores AI agent conversations against a CSV **Leaderboard Card** — a human-readable specification of what a good agent response looks like.

## How it works

1. Define your evaluation criteria in a CSV file (the Leaderboard Card)
2. Pass a conversation and the card to `Judge.evaluate()`
3. The judge calls an LLM once per criterion, collecting a structured verdict with reasoning
4. Scores are computed separately for `MUST-HAVE` and `SHOULD-HAVE` criteria
5. A configurable badge threshold (e.g. DIAMOND / GOLD / SILVER) is resolved from the scores

## Installation

```bash
pip install -r requirements.txt
```

**Dependencies:** `openai`, `instructor`, `pydantic`

Works with any OpenAI-compatible API via the `base_url` parameter.

## Leaderboard Card format

A CSV file with the following columns:

| Column | Description |
|---|---|
| `ID` | Unique check identifier, e.g. `LC-001` |
| `Category` | Grouping label, e.g. `Safety`, `Onboarding` |
| `Priority` | `MUST-HAVE` or `SHOULD-HAVE` |
| `Criterion` | What the agent must do |
| `Verification` | How to verify it from the conversation |
| `Pos Examples (Pass)` | Semicolon-separated examples that pass |
| `Neg Examples (Fail)` | Semicolon-separated examples that fail |

Rows with a blank `ID` are treated as spacers and skipped.

See [`tests/fixtures/sample_card.csv`](tests/fixtures/sample_card.csv) for a minimal example.

## Usage

```python
from judge import Judge, ScoringConfig, BadgeThreshold

judge = Judge(
    api_key="sk-...",
    base_url="https://api.openai.com/v1",
    model="gpt-4o-mini",
)

scoring_config = ScoringConfig(thresholds=[
    BadgeThreshold(label="DIAMOND", min_must_have=100.0, min_should_have=85.0),
    BadgeThreshold(label="GOLD",    min_must_have=100.0, min_should_have=70.0),
    BadgeThreshold(label="SILVER",  min_must_have=80.0,  min_should_have=50.0),
    BadgeThreshold(label="REJECTED",min_must_have=0.0,   min_should_have=0.0),
])

conversation = [
    {"role": "user",      "content": "Hi, I want some coaching help."},
    {"role": "assistant", "content": "Hi! I'm Alex, your coach. What brings you here today?"},
]

result = judge.evaluate(
    conversation,
    leaderboard_card="path/to/card.csv",
    scoring_config=scoring_config,
    on_progress=lambda done, total: print(f"  {done}/{total}"),
)

result.print_report()
```

**Output:**

```
=== EVALUATION REPORT ===

MUST-HAVE:    2/2  (100.0%)
SHOULD-HAVE:  1/1  (100.0%)
BADGE:        DIAMOND

✅ LC-001  [Onboarding]  Coach introduces itself by name
✅ LC-002  [Safety]      Coach never gives direct advice
✅ LC-003  [Engagement]  Coach uses open questions
```

## Smoke test

Run the end-to-end integration test against the sample card:

```bash
OPENAI_API_KEY=sk-... python smoke_test.py
OPENAI_API_KEY=sk-... python smoke_test.py --model gpt-4o
```

## Running tests

```bash
pytest          # from the repo root
pytest -v       # with per-test output
```

39 tests covering card parsing, scoring logic, evaluation loop, and retry behaviour. All tests use a mocked LLM — no API key required.

## API reference

### `Judge(api_key, base_url, model, max_retries=2)`

| Parameter | Description |
|---|---|
| `api_key` | API key for the LLM provider |
| `base_url` | Base URL of an OpenAI-compatible API |
| `model` | Model name, e.g. `gpt-4o-mini` |
| `max_retries` | Retries per check before recording a failed judgement |

### `Judge.evaluate(conversation, leaderboard_card, scoring_config=None, on_progress=None)`

| Parameter | Description |
|---|---|
| `conversation` | `list[dict]` with `role` and `content` keys |
| `leaderboard_card` | Path to CSV file or file-like object |
| `scoring_config` | `ScoringConfig` with badge thresholds (optional) |
| `on_progress` | `Callable[[int, int], None]` called after each check |

Returns an `EvaluationResult` with `must_have_score`, `should_have_score`, `badge`, `check_results`, and `print_report()`.
