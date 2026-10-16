import httpx

from tests.conftest import writes
from tests.factories import SHEET_ID, page, sheet_json

OTHER_ID = "2222222222222222"
COLUMNS = {
    "totalPages": 1,
    "data": [
        {"id": 1, "title": "Tarea", "index": 0, "primary": True, "type": "TEXT_NUMBER"},
        {"id": 10, "title": "Designer1", "index": 1, "type": "PICKLIST"},
    ],
}


def rule_json(rule_id: int, enabled: bool, column: int | None, reason: str | None = None) -> dict:
    return {
        "id": rule_id,
        "name": f"Regla {rule_id}",
        "enabled": enabled,
        "disabledReason": reason,
        "action": {
            "type": "NOTIFICATION_ACTION",
            "frequency": "IMMEDIATELY",
            "recipients": [],
            "recipientColumnIds": [column] if column else [],
            "notifyAllSharedUsers": False,
        },
    }


async def test_sheet_view(client, smartsheet) -> None:
    smartsheet.get(f"/sheets/{SHEET_ID}/columns").respond(json=COLUMNS)
    smartsheet.get(f"/sheets/{SHEET_ID}/automationrules").respond(
        json=page([rule_json(1, True, 10), rule_json(2, False, None, "NO_POTENTIAL_RECIPIENTS")])
    )
    body = (await client.get(f"/api/sheets/{SHEET_ID}/automations")).json()
    first, second = body["automations"]
    assert first["status"] == "with_problems"
    assert [p["code"] for p in first["problems"]] == ["RECIPIENT_COLUMN_NOT_CONTACT"]
    assert first["recipient_columns"][0]["title"] == "Designer1"
    assert second["status"] == "disabled"
    assert body["counts"] == {"with_problems": 1, "disabled": 1}
    assert writes(smartsheet) == []


async def test_account_view(client, smartsheet) -> None:
    smartsheet.get("/sheets").respond(json=page([sheet_json(), sheet_json(OTHER_ID, "Otra")]))
    smartsheet.get(f"/sheets/{SHEET_ID}/columns").respond(json=COLUMNS)
    smartsheet.get(f"/sheets/{SHEET_ID}/automationrules").respond(
        json=page([rule_json(1, True, 10)])
    )
    smartsheet.get(f"/sheets/{OTHER_ID}/automationrules").mock(
        return_value=httpx.Response(404, json={"errorCode": 1006})
    )
    body = (await client.get("/api/automations", params={"only_problems": True})).json()
    assert (body["sheets_reviewed"], body["rules_total"]) == (1, 1)
    assert body["by_problem"] == {"RECIPIENT_COLUMN_NOT_CONTACT": 1}
    assert [row["sheet_id"] for row in body["sheets"]] == [SHEET_ID]
    assert [f["sheet_id"] for f in body["failed_sheets"]] == [OTHER_ID]
    assert writes(smartsheet) == []
