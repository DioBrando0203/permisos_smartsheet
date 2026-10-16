from app.models.people import Person
from app.services.permissions import ShareType
from app.services.smartsheet import RawRow
from app.services.workload_rules import designers_in_row, match_person, phase_of, row_state

CLOSED = {"complete", "4. permit closed"}


def test_status_and_phase() -> None:
    assert row_state("COMPLETE", CLOSED) == "closed"
    assert row_state(" 4. Permit Closed ", CLOSED) == "closed"
    assert row_state("2. Design on Hold", CLOSED) == "on_hold"
    assert row_state("2. Design Process", CLOSED) == "open"
    assert row_state("-------", CLOSED) == "open" and row_state(None, CLOSED) == "open"
    assert phase_of("2. Design Process") == "2" and phase_of("IN PROGRESS") == "other"


def test_same_designer_in_two_columns() -> None:
    row = RawRow(
        "1", 1, None, None, None, None, None, cells={"a": "Ana Pérez", "b": "ana perez", "c": None}
    )
    assert designers_in_row(row, ["a", "b", "c"], {"designer1"}) == ["Ana Pérez"]
    header = RawRow("2", 2, None, None, None, None, None, cells={"a": "Designer1", "b": "---"})
    assert designers_in_row(header, ["a", "b"], {"designer1"}) == []


def person(key: str, name: str | None) -> Person:
    return Person(
        key=key,
        type=ShareType.USER,
        name=name,
        email=key,
        sheet_count=1,
        is_contact=False,
        is_org_member=False,
        is_token_owner=False,
    )


def test_match_person() -> None:
    people = [person("a@e.com", "Gonzalo Díaz"), person("b@e.com", "Ana"), person("c@e.com", "ana")]
    assert match_person("gonzalo diaz", people) == (people[0], False)
    assert match_person("Ana", people) == (None, True)
    assert match_person("Nadie", people) == (None, False)
