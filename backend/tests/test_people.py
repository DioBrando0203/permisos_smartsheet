import httpx
import respx

from tests.factories import SHEET_ID, page, share_json, sheet_json

OTHER_ID = "2222222222222222"


def _two_sheets(smartsheet: respx.MockRouter) -> None:
    smartsheet.get("/sheets").respond(
        json=page([sheet_json(), sheet_json(OTHER_ID, "Ñandú Fase 2")])
    )

    def shares(request: httpx.Request) -> httpx.Response:
        if request.url.params["assetId"] == OTHER_ID:
            items = [share_json("X1", "ana@example.com", "ADMIN")]
        else:
            items = [
                share_json("S-ANA", "ana@example.com", "EDITOR"),
                share_json("S-ANA", "ana@example.com", "VIEWER", "WORKSPACE"),
            ]
        return httpx.Response(200, json={"items": items})

    smartsheet.get("/shares").mock(side_effect=shares)
    smartsheet.get("/contacts").respond(
        json=page(
            [{"id": "c1", "email": "Ana@example.com"}, {"id": "c2", "email": "sola@example.com"}]
        )
    )


async def test_aggregates_person_across_sheets_and_contacts(client, smartsheet) -> None:
    _two_sheets(smartsheet)
    people = {p["key"]: p for p in (await client.get("/api/users")).json()["people"]}
    ana = people["ana@example.com"]
    assert (ana["sheet_count"], ana["highest_level"], ana["is_contact"]) == (2, "ADMIN", True)
    assert people["sola@example.com"]["sheet_count"] == 0


async def test_filters_and_search(client, smartsheet) -> None:
    _two_sheets(smartsheet)
    without = (await client.get("/api/users", params={"only": "without_access"})).json()
    assert [p["key"] for p in without["people"]] == ["sola@example.com"]
    found = (await client.get("/api/users", params={"q": "ANA"})).json()
    assert [p["key"] for p in found["people"]] == ["ana@example.com"]


async def test_person_detail_lists_sheets(client, smartsheet) -> None:
    _two_sheets(smartsheet)
    detail = (await client.get("/api/users/ana@example.com")).json()
    names = [(s["sheet_name"], s["scope"]) for s in detail["sheets"]]
    assert ("Ñandú Fase 2", "ITEM") in names and ("Plan 2026", "WORKSPACE") in names


async def test_failed_sheet_marks_incomplete(client, smartsheet) -> None:
    _two_sheets(smartsheet)

    def flaky(request: httpx.Request) -> httpx.Response:
        if request.url.params["assetId"] == OTHER_ID:
            return httpx.Response(404, json={"errorCode": 1006})
        return httpx.Response(200, json={"items": [share_json("S-ANA", "ana@example.com")]})

    smartsheet.get("/shares").mock(side_effect=flaky)
    body = (await client.get("/api/users")).json()
    assert body["incomplete"] is True
    assert body["failed_sheets"][0]["code"] == "SHEET_NOT_FOUND"
    assert body["people"][0]["key"] == "ana@example.com"


async def test_unknown_person_is_404(client, smartsheet) -> None:
    response = await client.get("/api/users/nadie@example.com")
    assert response.json()["detail"]["code"] == "PERSON_NOT_FOUND"


async def test_sheets_search_ignores_case_and_accents(client) -> None:
    response = await client.get("/api/sheets", params={"q": "PLAN"})
    body = response.json()
    assert body["total"] == 1 and body["sheets"][0]["id"] == SHEET_ID
    assert body["sheets"][0]["can_manage_shares"] is True


async def test_sheet_can_be_found_by_permalink_code(client, smartsheet) -> None:
    code = f"Pk{SHEET_ID}Code"
    by_code = await client.get(f"/api/sheets/{code}/shares")
    assert by_code.status_code == 200 and by_code.json()["sheet_id"] == SHEET_ID
    unknown = await client.get("/api/sheets/CodigoQueNoExiste123/shares")
    assert unknown.json()["detail"]["code"] == "SHEET_NOT_FOUND"
    shares_calls = [c for c in smartsheet.calls if c.request.url.path.endswith("/shares")]
    assert len(shares_calls) == 1


async def test_dynamic_view_mark_comes_from_settings(make_client, smartsheet) -> None:
    client = make_client(app_dynamic_view_sheets=f" {SHEET_ID} ,")
    sheet = (await client.get(f"/api/sheets/{SHEET_ID}")).json()
    assert sheet["has_dynamic_view"] is True
    audit = (await client.get(f"/api/sheets/{SHEET_ID}/audit")).json()
    assert audit["sheet"]["has_dynamic_view"] is True


async def test_org_member_last_login(client, smartsheet) -> None:
    route = smartsheet.get("/users").respond(
        json=page([{"id": 7, "email": "ana@example.com", "lastLogin": "2026-09-01T10:00:00Z"}])
    )
    _two_sheets(smartsheet)
    people = {p["key"]: p for p in (await client.get("/api/users")).json()["people"]}
    assert people["ana@example.com"]["last_login"].startswith("2026-09-01")
    assert people["sola@example.com"]["last_login"] is None
    assert route.calls.last.request.url.params["include"] == "lastLogin"
