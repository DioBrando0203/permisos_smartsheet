from datetime import UTC, datetime, timedelta

from app.services.activity_rules import (
    dominance_warning,
    editor_stats,
    idle_editors,
    rows_since,
)
from app.services.bulk_plans import effective_levels
from app.services.permissions import AccessLevel, ShareScope, ShareType
from app.services.smartsheet import RawAuthor, RawRow, RawShare

NOW = datetime(2026, 10, 16, tzinfo=UTC)


def raw_row(row_id: str, email: str | None, days_ago: int) -> RawRow:
    author = RawAuthor(email=email, name=None) if email else None
    return RawRow(row_id, 1, None, None, None, NOW - timedelta(days=days_ago), author)


def raw_share(email: str, level: str) -> RawShare:
    return RawShare(
        f"s-{email}", ShareType.USER, email, None, email, None, AccessLevel(level), ShareScope.ITEM
    )


def test_rows_since_filters_and_orders() -> None:
    rows = [raw_row("a", "x@e.com", 10), raw_row("b", "x@e.com", 1), raw_row("c", None, 40)]
    assert [r.id for r in rows_since(rows, NOW - timedelta(days=30))] == ["b", "a"]


def test_idle_editors() -> None:
    people = effective_levels(
        [
            raw_share("duena@e.com", "OWNER"),
            raw_share("activa@e.com", "EDITOR"),
            raw_share("quieta@e.com", "ADMIN"),
            raw_share("visor@e.com", "VIEWER"),
        ]
    )
    recent = [raw_row("1", "activa@e.com", 1)]
    assert [i.email for i in idle_editors(recent, people)] == ["quieta@e.com"]


def test_editor_stats_counts_rows_and_ignores_unknown_author() -> None:
    people = effective_levels([raw_share("a@e.com", "EDITOR")])
    recent = [raw_row("1", "a@e.com", 1), raw_row("2", "a@e.com", 2), raw_row("3", None, 1)]
    (stat,) = editor_stats(recent, people)
    assert (stat.email, stat.rows_changed, stat.access_level) == ("a@e.com", 2, AccessLevel.EDITOR)


def test_dominance_warning_when_one_account_hides_the_rest() -> None:
    people = effective_levels([raw_share("bot@e.com", "EDITOR"), raw_share("a@e.com", "EDITOR")])
    recent = [raw_row(str(n), "bot@e.com", 1) for n in range(9)] + [raw_row("x", "a@e.com", 1)]
    editors = editor_stats(recent, people)
    assert "90%" in (dominance_warning(editors, len(recent)) or "")
    balanced = editor_stats(recent[:5] + [raw_row(f"y{n}", "a@e.com", 1) for n in range(5)], people)
    assert dominance_warning(balanced, 10) is None
