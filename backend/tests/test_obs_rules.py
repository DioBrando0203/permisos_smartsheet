"""Reglas puras de Obs (SPEC-B17 CA-01, CA-02, CA-04 y CA-08): sin Smartsheet ni base de datos."""

from datetime import UTC, datetime
from zoneinfo import ZoneInfo

from app.services.obs import rules
from app.services.smartsheet.types import RawComment

LIMA = ZoneInfo("America/Lima")


def comment(cid: str, text: str, when: str, row: str = "1") -> RawComment:
    return RawComment(id=cid, row_id=row, text=text, created_at=datetime.fromisoformat(when))


def at(day: int, hour: int) -> str:
    """Hora UTC de noviembre de 2026; las 17:00 UTC son las 12:00 en Lima."""
    return f"2026-11-{day:02d}T{hour:02d}:00:00+00:00"


def test_compose_groups_by_local_day_in_order() -> None:
    items = [
        comment("3", "Permit picked.", "2026-11-13T15:00:00+00:00"),
        comment("1", "Sent the app.", "2026-11-12T17:38:00+00:00"),
        # 22:00 en Lima sigue siendo el 12 aunque en UTC ya sea el 13.
        comment("2", "Called the city.\nNo answer.", "2026-11-13T03:00:00+00:00"),
    ]
    assert rules.compose(None, items, LIMA) == (
        "11.13 - Permit picked.\n11.12 - Sent the app. // Called the city. // No answer."
    )


def test_internal_empty_and_archive_comments_are_skipped() -> None:
    for text in ("#interno revisar", "#INTERNAL note", "   ", "[Obs archive] 11.12.2026\nold"):
        assert rules.is_skipped(text)
    assert not rules.is_skipped("Permit approved")
    items = [comment("1", "#interno no", "2026-11-12T17:00:00+00:00")]
    assert rules.compose("x", items, LIMA) == "x"


def test_compose_prepends_and_joins_first_line_of_same_day() -> None:
    current = "11.12 - Sent the app.\n10.08 -  Awaiting confirmation."
    items = [
        comment("1", "Called the city.", at(12, 20)),
        comment("2", "Permit picked.", at(13, 17)),
    ]
    assert rules.compose(current, items, LIMA) == (
        "11.13 - Permit picked.\n"
        "11.12 - Sent the app. // Called the city.\n"
        "10.08 -  Awaiting confirmation."
    )


def test_compose_keeps_manual_text_and_handles_empty_obs() -> None:
    a, b = comment("1", "a", at(12, 17)), comment("2", "b", at(13, 17))
    assert rules.compose("Related to X", [a], LIMA) == "11.12 - a\nRelated to X"
    assert rules.compose(None, [a, b], LIMA) == "11.13 - b\n11.12 - a"
    assert rules.compose("Related to X", [], LIMA) == "Related to X"


def test_titles_open_sections_on_top() -> None:
    items = [
        comment("1", "a", at(12, 15)),
        comment("2", "**Permit", at(12, 16)),
        comment("3", "b", at(12, 17)),
        comment("4", "c", at(12, 18)),
        comment("5", "** Fees\nstage 2", at(13, 15)),
        comment("6", "d", at(13, 16)),
    ]
    assert rules.compose("10.08 - old", items, LIMA) == (
        "** Fees // stage 2\n11.13 - d\n\n**Permit\n11.12 - b // c\n\n11.12 - a\n10.08 - old"
    )
    assert rules.compose(None, items[1:3], LIMA) == "**Permit\n11.12 - b"


def test_entries_go_below_titles_written_by_hand() -> None:
    block = "** Permit extension #2\n**For updates see ROW line\n07.14 - old"
    new = [comment("1", "x", at(12, 17))]
    assert rules.compose(block, new, LIMA) == (
        "** Permit extension #2\n**For updates see ROW line\n11.12 - x\n07.14 - old"
    )
    same_day = "** ON ZAYO SIDE\n11.12 - a"
    assert rules.compose(same_day, new, LIMA) == "** ON ZAYO SIDE\n11.12 - a // x"


def test_fit_archives_oldest_lines_without_losing_text() -> None:
    value = "11.13 - new\n11.12 - middle\n10.08 - oldest"
    kept, archived = rules.fit(value, limit=26)
    assert kept == "11.13 - new\n11.12 - middle"
    assert archived == "10.08 - oldest"
    assert rules.fit("short", limit=26) == ("short", "")


def test_fit_truncates_single_long_line_and_archives_it_whole() -> None:
    line = "11.12 - " + "x" * 50
    kept, archived = rules.fit(line, limit=20)
    assert len(kept) == 20 and kept.endswith("…")
    assert archived == line


def test_archive_comments_are_marked_and_split() -> None:
    parts = rules.archive_comments("a" * 50, "11.12.2026", limit=40)
    header = "[Obs archive] 11.12.2026\n"
    assert all(part.startswith(header) and len(part) <= 40 for part in parts)
    assert "".join(part.removeprefix(header) for part in parts) == "a" * 50
    assert all(rules.is_skipped(part) for part in parts)


def test_day_label_uses_month_and_day() -> None:
    assert rules.day_label(datetime(2026, 1, 5, 18, tzinfo=UTC), LIMA) == "01.05"
