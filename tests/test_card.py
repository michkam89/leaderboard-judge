import io
import pytest
from pathlib import Path
from judge.card import load_card, CardParseError

FIXTURE = Path(__file__).parent / "fixtures" / "sample_card.csv"


def test_load_card_from_path():
    checks = load_card(FIXTURE)
    assert len(checks) == 3  # blank-ID row is skipped
    assert checks[0].id == "LC-001"
    assert checks[1].id == "LC-002"
    assert checks[2].id == "LC-003"


def test_load_card_categories():
    checks = load_card(FIXTURE)
    assert checks[0].category == "Onboarding"
    assert checks[2].category == "Engagement"


def test_load_card_priorities():
    checks = load_card(FIXTURE)
    assert checks[0].priority == "MUST-HAVE"
    assert checks[2].priority == "SHOULD-HAVE"


def test_load_card_splits_examples_on_semicolon():
    checks = load_card(FIXTURE)
    # sample_card.csv LC-001 pos: "Hi I'm Alex, your coach;Hello, I am Nova — your coach"
    assert checks[0].positive_examples == ["Hi I'm Alex, your coach", "Hello, I am Nova — your coach"]
    assert len(checks[0].negative_examples) == 2


def test_load_card_from_file_object():
    with open(FIXTURE) as f:
        checks = load_card(f)
    assert len(checks) == 3


def test_load_card_from_string_io():
    csv = (
        "ID,Category,Priority,Criterion,Verification,"
        "Pos Examples (Pass),Neg Examples (Fail)\n"
        "LC-001,Onboarding,MUST-HAVE,Intro,Check first,Good example,Bad example\n"
    )
    checks = load_card(io.StringIO(csv))
    assert len(checks) == 1
    assert checks[0].id == "LC-001"


def test_load_card_empty_examples_become_empty_list():
    csv = (
        "ID,Category,Priority,Criterion,Verification,"
        "Pos Examples (Pass),Neg Examples (Fail)\n"
        "LC-001,Onboarding,MUST-HAVE,Intro,Check first,,\n"
    )
    checks = load_card(io.StringIO(csv))
    assert checks[0].positive_examples == []
    assert checks[0].negative_examples == []


def test_load_card_blank_id_row_skipped():
    csv = (
        "ID,Category,Priority,Criterion,Verification,"
        "Pos Examples (Pass),Neg Examples (Fail)\n"
        "LC-001,Onboarding,MUST-HAVE,Intro,Check first,Good,Bad\n"
        ",,,,,, \n"
    )
    checks = load_card(io.StringIO(csv))
    assert len(checks) == 1


def test_load_card_missing_required_column_raises():
    csv = "ID,Category,Priority,Criterion\nLC-001,Onboarding,MUST-HAVE,Intro\n"
    with pytest.raises(CardParseError, match="Verification"):
        load_card(io.StringIO(csv))


def test_load_card_duplicate_ids_raises():
    csv = (
        "ID,Category,Priority,Criterion,Verification,"
        "Pos Examples (Pass),Neg Examples (Fail)\n"
        "LC-001,Onboarding,MUST-HAVE,Intro,Check first,Good,Bad\n"
        "LC-001,Safety,MUST-HAVE,Other,Check all,Good,Bad\n"
    )
    with pytest.raises(CardParseError, match="LC-001"):
        load_card(io.StringIO(csv))


def test_load_card_invalid_priority_raises():
    csv = (
        "ID,Category,Priority,Criterion,Verification,"
        "Pos Examples (Pass),Neg Examples (Fail)\n"
        "LC-001,Onboarding,NICE-TO-HAVE,Intro,Check first,Good,Bad\n"
    )
    with pytest.raises(CardParseError, match="row 2"):
        load_card(io.StringIO(csv))


def test_load_card_custom_delimiter():
    csv = (
        "ID,Category,Priority,Criterion,Verification,"
        "Pos Examples (Pass),Neg Examples (Fail)\n"
        "LC-001,Onboarding,MUST-HAVE,Intro,Check first,Good|Better,Bad|Worse\n"
    )
    checks = load_card(io.StringIO(csv), example_delimiter="|")
    assert checks[0].positive_examples == ["Good", "Better"]
