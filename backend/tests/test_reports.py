import httpx
import respx

from tests.conftest import writes
from tests.factories import OWNER_EMAIL, SHEET_ID, page, share_json, sheet_json

OTHER_ID = "2222222222222222"


def two_sheets(smartsheet: respx.MockRouter, shares_a: list, shares_b: list) -> None:
    smartsheet.get("/sheets").respond(
        json=page([sheet_json(), sheet_json(OTHER_ID, "Plan 2025", level="OWNER")])
    )
    smartsheet.get("/shares").mock(
        side_effect=lambda request: httpx.Response(
            200,
            json={"items": shares_b if request.url.params["assetId"] == OTHER_ID else shares_a},
        )
    )


async def test_audit_flags_external_admin(client, smartsheet) -> None:
    smartsheet.get("/users").respond(json=page([{"id": 1, "email": "interna@example.com"}]))
    smartsheet.get("/shares").respond(
        json={
            "items": [
                share_json("S1", OWNER_EMAIL, "OWNER"),
                share_json("S2", "socio@example.com", "ADMIN", name="Socio"),
                share_json("S3", "interna@example.com", "ADMIN", name="Interna"),
                share_json("S4", "casa@hotmail.com", "EDITOR"),
            ]
        }
    )
    body = (await client.get(f"/api/sheets/{SHEET_ID}/audit")).json()
    alerts = {alert["code"]: alert for alert in body["alerts"]}
    assert [p["email"] for p in alerts["EXTERNAL_CAN_SHARE"]["people"]] == ["socio@example.com"]
    assert alerts["PERSONAL_EMAIL_CAN_EDIT"]["count"] == 1
    assert body["by_level"] == {"OWNER": 1, "ADMIN": 2, "EDITOR": 1}
    assert {d["domain"]: d["is_personal"] for d in body["by_domain"]}["hotmail.com"] is True
    assert body["org_known"] is True and body["external_count"] == 3
    assert writes(smartsheet) == []


async def test_compare_sheets(client, smartsheet) -> None:
    a = [
        share_json("A1", "ana@example.com", "EDITOR"),
        share_json("A2", "luis@example.com", "VIEWER"),
        share_json("A3", "bea@example.com", "VIEWER", "WORKSPACE"),
    ]
    b = [
        share_json("B1", "ana@example.com", "EDITOR"),
        share_json("B2", "bea@example.com", "ADMIN"),
        share_json("B3", "nuevo@example.com", "VIEWER"),
    ]
    two_sheets(smartsheet, a, b)
    body = (await client.get("/api/sheets/compare", params={"a": SHEET_ID, "b": OTHER_ID})).json()
    assert [p["key"] for p in body["only_in_a"]] == ["luis@example.com"]
    assert [p["key"] for p in body["only_in_b"]] == ["nuevo@example.com"]
    diff = body["level_differences"][0]
    assert (diff["key"], diff["level_a"], diff["level_b"]) == ("bea@example.com", "VIEWER", "ADMIN")
    assert body["same_count"] == 1


async def test_compare_same_sheet(client) -> None:
    response = await client.get("/api/sheets/compare", params={"a": SHEET_ID, "b": SHEET_ID})
    assert response.json()["detail"]["code"] == "SAME_SHEET"


async def test_access_summary(client, smartsheet) -> None:
    a = [share_json("O", OWNER_EMAIL, "OWNER"), share_json("A1", "x@hotmail.com", "EDITOR")]
    b = [share_json("B1", "y@example.com", "VIEWER")]
    two_sheets(smartsheet, a, b)
    body = (await client.get("/api/sheets/access-summary", params={"inactive_days": 1})).json()
    rows = {row["sheet_id"]: row for row in body["sheets"]}
    assert rows[SHEET_ID]["share_count"] == 1  # sin contar al propietario
    assert rows[SHEET_ID]["personal_email_count"] == 1
    assert rows[SHEET_ID]["editors_count"] == 1 and rows[OTHER_ID]["editors_count"] == 0
    assert rows[SHEET_ID]["is_inactive"] is True  # modificada en 2026-10-01
