import json

import httpx
import respx

from tests.conftest import writes
from tests.factories import SHEET_ID, share_json, sheet_json

SHARES = f"/api/sheets/{SHEET_ID}/shares"


async def test_list_marks_owner_and_inherited_as_locked(client: httpx.AsyncClient) -> None:
    response = await client.get(SHARES)
    assert response.status_code == 200
    shares = {share["id"]: share for share in response.json()["shares"]}
    assert shares["S-OWNER"]["locked_reason"] == "OWNER"
    assert shares["S-WS"]["locked_reason"] == "INHERITED"
    assert shares["S-ANA"]["editable"] is True
    assert [share["id"] for share in response.json()["shares"]][0] == "S-OWNER"


async def test_read_only_mode_blocks_every_write(make_client, smartsheet: respx.MockRouter) -> None:
    client = make_client(app_read_only=True)
    body = {"recipients": [{"email": "nueva@example.com"}], "access_level": "VIEWER"}
    responses = [
        await client.post(SHARES, json=body),
        await client.patch(f"{SHARES}/S-ANA", json={"access_level": "VIEWER"}),
        await client.delete(f"{SHARES}/S-ANA"),
    ]
    assert [r.json()["detail"]["code"] for r in responses] == ["READ_ONLY_MODE"] * 3
    assert smartsheet.calls.call_count == 0


async def test_cannot_create_owner(client: httpx.AsyncClient, smartsheet) -> None:
    body = {"recipients": [{"email": "x@example.com"}], "access_level": "OWNER"}
    response = await client.post(SHARES, json=body)
    assert response.json()["detail"]["code"] == "OWNER_NOT_ASSIGNABLE"
    assert writes(smartsheet) == []


async def test_duplicate_recipients_are_rejected(client: httpx.AsyncClient, smartsheet) -> None:
    body = {
        "recipients": [{"email": "A@example.com"}, {"email": "a@example.com"}],
        "access_level": "VIEWER",
    }
    response = await client.post(SHARES, json=body)
    assert response.json()["detail"]["code"] == "DUPLICATE_RECIPIENTS"
    assert writes(smartsheet) == []


async def test_create_skips_existing_and_does_not_email_by_default(
    client: httpx.AsyncClient, smartsheet: respx.MockRouter
) -> None:
    created = smartsheet.post("/shares").respond(json={"items": []})
    after = [share_json("S-NEW", "nueva@example.com", "VIEWER")]
    smartsheet.get("/shares").mock(
        side_effect=[
            httpx.Response(200, json={"items": [share_json("S-ANA", "ana@example.com")]}),
            httpx.Response(200, json={"items": after}),
        ]
    )
    body = {
        "recipients": [{"email": "ana@example.com"}, {"email": "nueva@example.com"}],
        "access_level": "VIEWER",
        "subject": "no debe viajar",
    }
    response = await client.post(SHARES, json=body)
    assert response.status_code == 201
    result = response.json()
    assert [share["id"] for share in result["created"]] == ["S-NEW"]
    assert result["skipped"][0]["reason"] == "ALREADY_SHARED"
    request = created.calls.last.request
    assert request.url.params["sendEmail"] == "false"
    assert request.url.params["assetType"] == "sheet"
    assert json.loads(request.content) == [{"accessLevel": "VIEWER", "email": "nueva@example.com"}]


async def test_owner_share_is_locked(client: httpx.AsyncClient, smartsheet) -> None:
    smartsheet.get("/shares/S-OWNER").respond(
        json=share_json("S-OWNER", "duena@example.com", "OWNER")
    )
    response = await client.delete(f"{SHARES}/S-OWNER")
    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "OWNER_LOCKED"
    assert writes(smartsheet) == []


async def test_inherited_share_is_locked(client: httpx.AsyncClient, smartsheet) -> None:
    smartsheet.get("/shares/S-WS").respond(
        json=share_json("S-WS", "beto@example.com", "ADMIN", "WORKSPACE")
    )
    response = await client.patch(f"{SHARES}/S-WS", json={"access_level": "VIEWER"})
    assert response.json()["detail"]["code"] == "SHARE_INHERITED"
    assert writes(smartsheet) == []


async def test_viewer_token_cannot_manage(client: httpx.AsyncClient, smartsheet) -> None:
    smartsheet.get(f"/sheets/{SHEET_ID}").respond(json=sheet_json(level="EDITOR"))
    smartsheet.get("/shares/S-ANA").respond(json=share_json("S-ANA", "ana@example.com"))
    response = await client.delete(f"{SHARES}/S-ANA")
    assert response.json()["detail"]["code"] == "CANNOT_MANAGE_SHARES"
    assert writes(smartsheet) == []


async def test_same_level_is_noop(client: httpx.AsyncClient, smartsheet) -> None:
    smartsheet.get("/shares/S-ANA").respond(json=share_json("S-ANA", "ana@example.com"))
    response = await client.patch(f"{SHARES}/S-ANA", json={"access_level": "EDITOR"})
    assert response.status_code == 200
    assert writes(smartsheet) == []


async def test_update_and_delete_send_expected_requests(
    client: httpx.AsyncClient, smartsheet: respx.MockRouter
) -> None:
    smartsheet.get("/shares/S-ANA").mock(
        side_effect=[
            httpx.Response(200, json=share_json("S-ANA", "ana@example.com", "EDITOR")),
            httpx.Response(200, json=share_json("S-ANA", "ana@example.com", "VIEWER")),
            httpx.Response(200, json=share_json("S-ANA", "ana@example.com", "VIEWER")),
        ]
    )
    patch = smartsheet.patch("/shares/S-ANA").respond(json={})
    delete = smartsheet.delete("/shares/S-ANA").respond(json={})
    updated = await client.patch(f"{SHARES}/S-ANA", json={"access_level": "VIEWER"})
    assert updated.json()["access_level"] == "VIEWER"
    assert json.loads(patch.calls.last.request.content) == {"accessLevel": "VIEWER"}
    removed = await client.delete(f"{SHARES}/S-ANA")
    assert removed.status_code == 204
    assert delete.calls.last.request.url.params["assetId"] == SHEET_ID


async def test_writes_invalidate_cache(client: httpx.AsyncClient, smartsheet) -> None:
    smartsheet.get("/shares/S-ANA").respond(json=share_json("S-ANA", "ana@example.com"))
    smartsheet.delete("/shares/S-ANA").respond(json={})
    await client.get(SHARES)
    first = _list_calls(smartsheet)
    await client.get(SHARES)
    assert _list_calls(smartsheet) == first
    await client.delete(f"{SHARES}/S-ANA")
    await client.get(SHARES)
    assert _list_calls(smartsheet) == first + 1


def _list_calls(router: respx.MockRouter) -> int:
    return sum(1 for call in router.calls if call.request.url.path.endswith("/shares"))


async def test_invalid_ids_never_reach_smartsheet(client: httpx.AsyncClient, smartsheet) -> None:
    for bad in ("abc-def", "a.b", "x" * 65):
        response = await client.get(f"/api/sheets/{bad}/shares")
        assert response.status_code == 422, bad
    assert smartsheet.calls.call_count == 0
