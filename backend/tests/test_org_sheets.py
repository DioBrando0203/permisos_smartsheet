from tests.conftest import writes
from tests.factories import SHEET_ID, page, sheet_json

ORG_ID = "3333333333333333"


def with_org_sheet(smartsheet) -> None:
    smartsheet.get("/users/sheets").respond(
        json=page(
            [
                {"id": int(SHEET_ID), "name": "Plan 2026", "owner": "Duena@example.com"},
                {"id": int(ORG_ID), "name": "Plan ajeno", "owner": "otra@example.com"},
            ]
        )
    )


async def test_org_sheets_are_listed_and_marked(client, smartsheet) -> None:
    with_org_sheet(smartsheet)
    body = (await client.get("/api/sheets")).json()
    assert (body["total"], body["total_mine"]) == (2, 1)
    sheets = {sheet["id"]: sheet for sheet in body["sheets"]}
    assert sheets[SHEET_ID]["in_my_list"] is True
    assert sheets[SHEET_ID]["owner_email"] == "duena@example.com"
    other = sheets[ORG_ID]
    assert (other["in_my_list"], other["access_level"], other["can_manage_shares"]) == (
        False,
        None,
        False,
    )
    only = (await client.get("/api/sheets", params={"scope": "org_only"})).json()
    assert [sheet["id"] for sheet in only["sheets"]] == [ORG_ID]


async def test_org_sheet_shares_are_read_only(client, smartsheet) -> None:
    with_org_sheet(smartsheet)
    shares = (await client.get(f"/api/sheets/{ORG_ID}/shares")).json()["shares"]
    assert shares and all(
        s["locked_reason"] in {"OWNER", "INHERITED", "NO_PERMISSION"} for s in shares
    )
    response = await client.delete(f"/api/sheets/{ORG_ID}/shares/S-ANA")
    assert response.json()["detail"]["code"] == "NOT_SHARED_WITH_TOKEN"
    assert writes(smartsheet) == []


async def test_org_list_forbidden_falls_back_to_mine(client, smartsheet) -> None:
    smartsheet.get("/users/sheets").respond(403, json={"errorCode": 1004})
    body = (await client.get("/api/sheets")).json()
    assert body["total"] == body["total_mine"] == 1


async def test_sheet_json_still_maps_level(client) -> None:
    assert (await client.get(f"/api/sheets/{SHEET_ID}")).json()["access_level"] == sheet_json()[
        "accessLevel"
    ]
