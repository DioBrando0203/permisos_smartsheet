"""Orden y aislamiento del procesador de IDs, sin escritura real."""

from unittest.mock import AsyncMock

from app.services.ids.connector import Outcome
from app.services.ids.processor import process_report


async def test_processor_orders_dependencies_and_skips_pending() -> None:
    connector = AsyncMock()
    connector.process.return_value = Outcome.CONFIRMED
    report = {
        "pending_or_conflicting_rows": [
            {
                "sheet_id": "3",
                "row_id": "1",
                "type": "record",
                "parent": "T",
                "action": "needs_reservation",
            },
            {
                "sheet_id": "2",
                "row_id": "2",
                "type": "task",
                "parent": "P",
                "action": "pending_parent",
            },
            {
                "sheet_id": "1",
                "row_id": "3",
                "type": "project",
                "parent": "KMV-BS-27",
                "action": "pending_formula",
            },
            {
                "sheet_id": "2",
                "row_id": "4",
                "type": "task",
                "parent": "P",
                "action": "needs_reservation",
            },
        ]
    }
    assert await process_report(connector, report) == {"confirmed": 3}
    assert [call.args[0].kind.value for call in connector.process.await_args_list] == [
        "project",
        "task",
        "record",
    ]


async def test_processor_limit_defers_rows_and_reports_results() -> None:
    connector = AsyncMock()
    connector.process.side_effect = [Outcome.CONFIRMED, ValueError("sin rango")]
    rows = [
        {"sheet_id": "2", "row_id": str(n), "type": "task", "parent": "P", "action": "would_write"}
        for n in range(4)
    ]
    results: list[dict] = []
    counts = await process_report(
        connector, {"pending_or_conflicting_rows": rows}, limit=2, results=results
    )
    assert counts == {"confirmed": 1, "error": 1, "deferred": 2}
    assert [item["outcome"] for item in results] == ["confirmed", "error"]
    assert connector.process.await_count == 2
