import httpx
import respx

from tests.conftest import writes
from tests.factories import OWNER_EMAIL, SHEET_ID, page, share_json, sheet_json

OTHER_ID = "2222222222222222"
EXTERNAL_ADMIN = share_json("E", "socio@example.com", "ADMIN", name="Socio")


def two_sheets(smartsheet: respx.MockRouter, other_status: int = 200) -> None:
    smartsheet.get("/sheets").respond(json=page([sheet_json(), sheet_json(OTHER_ID, "Plan 2025")]))
    by_sheet = {
        SHEET_ID: [share_json("O", OWNER_EMAIL, "OWNER"), EXTERNAL_ADMIN],
        OTHER_ID: [EXTERNAL_ADMIN, share_json("H", "casa@hotmail.com", "EDITOR", name="Casa")],
    }

    def respond(request: httpx.Request) -> httpx.Response:
        sheet_id = request.url.params["assetId"]
        if sheet_id == OTHER_ID and other_status != 200:
            return httpx.Response(other_status, json={"errorCode": 1006})
        return httpx.Response(200, json={"items": by_sheet[sheet_id]})

    smartsheet.get("/shares").mock(side_effect=respond)
    smartsheet.get("/contacts").respond(
        json=page(
            [{"id": "c", "email": "socio@example.com"}, {"id": "d", "email": "casa@hotmail.com"}]
        )
    )


async def test_review_aggregates_sheets_and_people(client, smartsheet) -> None:
    two_sheets(smartsheet)
    body = (await client.get("/api/review")).json()
    assert body["totals"]["sheets_reviewed"] == 2 and body["totals"]["sheets_with_alerts"] == 2
    top = body["people"][0]
    assert (top["key"], top["sheet_count"], top["codes"]) == (
        "socio@example.com",
        2,
        ["EXTERNAL_CAN_SHARE"],
    )
    assert body["sheets"][0]["max_severity"] == "high"
    assert writes(smartsheet) == []


async def test_min_severity_filters(client, smartsheet) -> None:
    two_sheets(smartsheet)
    body = (await client.get("/api/review", params={"min_severity": "high"})).json()
    assert body["totals"]["people_by_code"] == {"EXTERNAL_CAN_SHARE": 1}
    assert all(set(row["alerts"]) == {"EXTERNAL_CAN_SHARE"} for row in body["sheets"])


async def test_failed_sheet_is_reported(client, smartsheet) -> None:
    two_sheets(smartsheet, other_status=404)
    body = (await client.get("/api/review")).json()
    assert [f["sheet_id"] for f in body["failed_sheets"]] == [OTHER_ID]
    assert body["totals"]["sheets_reviewed"] == 1
