"""`GET /api/ids/logs` (SPEC-B21 RG-02, CA-B21-02); Smartsheet simulado, datos sintéticos."""

import logging

from pydantic import SecretStr

TOKEN = "clave-sintetica-de-prueba"
HEADERS = {"Authorization": f"Bearer {TOKEN}"}


async def test_logs_need_the_id_manager_token(make_client, smartsheet) -> None:
    client = make_client(ids_admin_token=SecretStr(TOKEN))
    assert (await client.get("/api/ids/logs")).status_code == 401
    bad = await client.get("/api/ids/logs", headers={"Authorization": "Bearer mal"})
    assert bad.status_code == 401


async def test_logs_return_events_newest_first_and_api_usage(make_client, smartsheet) -> None:
    client = make_client(ids_admin_token=SecretStr(TOKEN))
    monitor = logging.getLogger("app.services.ids.monitor")
    monitor.error("ciclo: falló el paso records de persona1@example.com")
    monitor.error("ciclo: falló el paso permits")
    response = await client.get("/api/ids/logs?level=ERROR&contains=records", headers=HEADERS)
    assert response.status_code == 200
    body = response.json()
    assert [item["message"] for item in body["items"]] == [
        "ciclo: falló el paso records de <email>"
    ]
    assert body["capacity"] == 1000
    assert body["api"]["max_per_minute"] == 250 and body["api"]["rate_limited"] == 0


async def test_logs_validate_level_and_limit(make_client, smartsheet) -> None:
    client = make_client(ids_admin_token=SecretStr(TOKEN))
    for query in ("level=DEBUG", "limit=0", "limit=501"):
        assert (await client.get(f"/api/ids/logs?{query}", headers=HEADERS)).status_code == 422
