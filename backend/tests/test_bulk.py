import json

import httpx
import respx

from tests.conftest import writes
from tests.factories import OWNER_EMAIL, SHEET_ID, page, share_json, sheet_json

SOURCE_ID = "2222222222222222"
COPY = f"/api/sheets/{SHEET_ID}/shares/copy"


def setup(smartsheet: respx.MockRouter, source: list, target: list) -> None:
    smartsheet.get("/sheets").respond(json=page([sheet_json(), sheet_json(SOURCE_ID, "Plan 2025")]))
    smartsheet.get("/shares").mock(
        side_effect=lambda request: httpx.Response(
            200,
            json={"items": source if request.url.params["assetId"] == SOURCE_ID else target},
        )
    )


SOURCE = [
    share_json("S0", OWNER_EMAIL, "OWNER"),
    share_json("S1", "ana@example.com", "EDITOR"),
    share_json("S2", "luis@example.com", "ADMIN"),
    share_json("S3", "nuevo@example.com", "VIEWER"),
]
TARGET = [
    share_json("T0", OWNER_EMAIL, "OWNER"),
    share_json("T1", "ana@example.com", "EDITOR"),
    share_json("T2", "luis@example.com", "VIEWER"),
]


async def test_copy_plan_dry_run(client, smartsheet) -> None:
    setup(smartsheet, SOURCE, TARGET)
    body = (await client.post(COPY, json={"source_sheet_id": SOURCE_ID})).json()
    actions = {step["key"]: step["action"] for step in body["steps"]}
    assert actions == {
        OWNER_EMAIL: "SKIP",
        "ana@example.com": "KEEP",
        "luis@example.com": "KEEP",
        "nuevo@example.com": "CREATE",
    }
    assert body["dry_run"] is True and body["counts"]["CREATE"] == 1
    assert writes(smartsheet) == []


async def test_execute_blocked_in_read_only(make_client, smartsheet) -> None:
    setup(smartsheet, SOURCE, TARGET)
    client = make_client(app_read_only=True)
    copy = await client.post(COPY, json={"source_sheet_id": SOURCE_ID, "dry_run": False})
    revoke = await client.post("/api/users/ana@example.com/revoke", json={"dry_run": False})
    assert copy.json()["detail"]["code"] == "READ_ONLY_MODE"
    assert revoke.json()["detail"]["code"] == "READ_ONLY_MODE"
    assert writes(smartsheet) == []
    simulated = await client.post(COPY, json={"source_sheet_id": SOURCE_ID})
    assert simulated.status_code == 200


async def test_copy_execute_isolates_failures(client, smartsheet) -> None:
    setup(smartsheet, SOURCE, TARGET)
    create = smartsheet.post("/shares").respond(json={"items": []})
    smartsheet.get("/shares/T2").respond(json=share_json("T2", "luis@example.com", "VIEWER"))
    smartsheet.patch("/shares/T2").respond(500)
    body = {"source_sheet_id": SOURCE_ID, "upgrade_levels": True, "dry_run": False}
    result = (await client.post(COPY, json=body)).json()
    status = {step["key"]: (step["action"], step["status"]) for step in result["steps"]}
    assert status["nuevo@example.com"] == ("CREATE", "done")
    assert status["luis@example.com"] == ("UPGRADE", "failed")
    request = create.calls.last.request
    assert request.url.params["sendEmail"] == "false"
    assert json.loads(request.content) == [{"accessLevel": "VIEWER", "email": "nuevo@example.com"}]


async def test_revoke_plan(client, smartsheet) -> None:
    setup(
        smartsheet,
        [share_json("X1", "ana@example.com", "ADMIN", "WORKSPACE")],
        [share_json("T1", "ana@example.com", "EDITOR")],
    )
    body = (await client.post("/api/users/ana@example.com/revoke", json={})).json()
    steps = {step["sheet_id"]: (step["action"], step["reason"]) for step in body["steps"]}
    assert steps == {SHEET_ID: ("REMOVE", None), SOURCE_ID: ("SKIP", "INHERITED")}
    assert writes(smartsheet) == []


async def test_revoke_execute(client, smartsheet) -> None:
    setup(smartsheet, [], [share_json("T1", "ana@example.com", "EDITOR")])
    smartsheet.get("/shares/T1").respond(json=share_json("T1", "ana@example.com", "EDITOR"))
    delete = smartsheet.delete("/shares/T1").respond(json={})
    body = {"sheet_ids": [SHEET_ID], "dry_run": False}
    result = (await client.post("/api/users/ana@example.com/revoke", json=body)).json()
    assert [step["status"] for step in result["steps"]] == ["done"]
    assert delete.call_count == 1
