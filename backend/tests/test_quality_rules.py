import re

from app.services.quality_rules import compile_pattern, duplicates, issue_count, mismatches, missing
from app.services.smartsheet import RawRow


def row(row_id: str, **cells: str | None) -> RawRow:
    return RawRow(row_id, int(row_id), f"fila {row_id}", None, None, None, None, cells=cells)


ROWS = [
    row("1", rid="10521", des="Ana"),
    row("2", rid=" 10521 ", des=None),
    row("3", rid="ABC-1", des="  "),
    row("4", rid=None, des="Luis"),
    row("5", rid="abc-1", des="Ana"),
]


def test_duplicates() -> None:
    issues = duplicates(ROWS, "rid")
    assert [(i.value, [r.row_id for r in i.rows]) for i in issues] == [
        ("10521", ["1", "2"]),
        ("ABC-1", ["3", "5"]),
    ]
    assert issue_count(issues) == 4


def test_missing() -> None:
    (issue,) = missing(ROWS, "des")
    assert [r.row_id for r in issue.rows] == ["2", "3"]
    assert missing([row("9", des="x")], "des") == []


def test_mismatches_and_pattern_limits() -> None:
    issues = mismatches(ROWS, "rid", re.compile(r"^\d+$"))
    assert sorted(i.value for i in issues) == ["ABC-1", "abc-1"]
    assert compile_pattern("(") is None and compile_pattern("x" * 101) is None
    assert compile_pattern(r"^\d{5}$") is not None


def test_missing_references() -> None:
    from app.services.quality_rules import missing_references, normalized_values

    catalog = normalized_values([row("9", des=" ana "), row("8", des="Luis")], "des")
    assert catalog == {"ana", "luis"}
    issues = missing_references(
        ROWS + [row("6", des="Pepe"), row("7", des="pepe ")], "des", catalog
    )
    assert [(i.value, [r.row_id for r in i.rows]) for i in issues] == [("Pepe", ["6", "7"])]
