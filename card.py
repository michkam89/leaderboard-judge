from __future__ import annotations
import csv
from pathlib import Path
from typing import IO

from judge.models import CheckDefinition, MUST_HAVE, SHOULD_HAVE

REQUIRED_COLUMNS = {
    "ID",
    "Category",
    "Priority",
    "Criterion",
    "Verification",
    "Pos Examples (Pass)",
    "Neg Examples (Fail)",
}


class CardParseError(Exception):
    pass


def load_card(
    source: str | Path | IO,
    example_delimiter: str = ";",
) -> list[CheckDefinition]:
    if isinstance(source, (str, Path)):
        with open(source, newline="", encoding="utf-8") as f:
            return _parse(f, example_delimiter)
    return _parse(source, example_delimiter)


def _parse(f: IO, delimiter: str) -> list[CheckDefinition]:
    reader = csv.DictReader(f)

    missing = REQUIRED_COLUMNS - set(reader.fieldnames or [])
    if missing:
        raise CardParseError(f"Missing required column(s): {', '.join(sorted(missing))}")

    def split_examples(cell: str) -> list[str]:
        return [e.strip() for e in cell.split(delimiter) if e.strip()]

    checks: list[CheckDefinition] = []
    seen_ids: set[str] = set()

    for row_num, row in enumerate(reader, start=2):
        row_id = row["ID"].strip()
        if not row_id:
            continue

        if row_id in seen_ids:
            raise CardParseError(f"Duplicate ID '{row_id}' found at row {row_num}")
        seen_ids.add(row_id)

        priority = row["Priority"].strip().upper()
        if priority not in (MUST_HAVE, SHOULD_HAVE):
            raise CardParseError(
                f"Invalid Priority '{priority}' at row {row_num}. "
                f"Must be '{MUST_HAVE}' or '{SHOULD_HAVE}'."
            )

        checks.append(
            CheckDefinition(
                id=row_id,
                category=row["Category"].strip(),
                priority=priority,
                criterion=row["Criterion"].strip(),
                verification=row["Verification"].strip(),
                positive_examples=split_examples(row["Pos Examples (Pass)"]),
                negative_examples=split_examples(row["Neg Examples (Fail)"]),
            )
        )

    return checks
