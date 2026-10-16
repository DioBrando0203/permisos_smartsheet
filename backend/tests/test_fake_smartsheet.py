"""El backend completo contra el Smartsheet falso: el falso imita lo que el cliente espera.

Si una de estas pruebas falla tras cambiar el cliente, el falso dejó de parecerse a Smartsheet
y las pruebas E2E del frontend no serían confiables (ADR-10 del frontend).
"""

import csv
import io

import httpx
import pytest

from app.api.deps import build_services
from app.main import create_app
from app.services.smartsheet import SmartsheetClient
from tests import fake_data
from tests.conftest import make_settings
from tests.fake_smartsheet import create_fake_app

P26, P25 = fake_data.PLAN_2026, fake_data.PLAN_2025


@pytest.fixture
async def stack():
    fake = create_fake_app()
    settings = make_settings(app_designer_catalog_sheet=fake_data.CATALOG)
    transport = httpx.ASGITransport(app=fake)
    smartsheet_http = httpx.AsyncClient(transport=transport, base_url="http://fake/2.0")
    services = build_services(settings, SmartsheetClient(settings, smartsheet_http))
    app = create_app(settings, services, frontend_dist=None)
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://localhost"
    ) as client:
        yield client, fake.state.fake
    await smartsheet_http.aclose()


async def test_reads_through_the_fake(stack) -> None:
    client, _ = stack
    sheets = (await client.get("/api/sheets")).json()
    assert (sheets["total"], sheets["total_mine"]) == (4, 3)
    shares = (await client.get(f"/api/sheets/{P26}/shares")).json()["shares"]
    assert {(s["id"], s["scope"]) for s in shares} >= {("S-OWN", "ITEM"), ("S-OWN", "WORKSPACE")}
    people = {p["key"]: p for p in (await client.get("/api/users")).json()["people"]}
    assert people["sola@example.com"]["sheet_count"] == 0
    assert people["ana@example.com"]["last_login"] is not None
    foreign = (await client.get(f"/api/sheets/{fake_data.FOREIGN}/shares")).json()["shares"]
    assert foreign[0]["locked_reason"] == "OWNER"


async def test_reports_through_the_fake(stack) -> None:
    client, _ = stack
    audit = (await client.get(f"/api/sheets/{P26}/audit")).json()
    assert {a["code"] for a in audit["alerts"]} >= {"EXTERNAL_CAN_SHARE", "PERSONAL_EMAIL_CAN_EDIT"}
    compare = (await client.get("/api/sheets/compare", params={"a": P25, "b": P26})).json()
    assert [p["key"] for p in compare["only_in_a"]] == ["nuevo@example.com"]
    activity = (await client.get(f"/api/sheets/{P26}/activity", params={"days": 30})).json()
    assert activity["changed_rows_total"] == 4
    history = (await client.get(f"/api/sheets/{P26}/rows/7001/history")).json()
    assert history["changes"] and history["failed_columns"] == 0
    automations = (await client.get("/api/automations")).json()
    assert automations["by_problem"]["RECIPIENT_COLUMN_NOT_CONTACT"] == 1
    review = (await client.get("/api/review")).json()
    assert review["totals"]["sheets_reviewed"] == 4


async def test_data_quality_and_designers_through_the_fake(stack) -> None:
    client, _ = stack
    params = {"unique": "Record ID", "required": "Designer1"}
    quality = (await client.get(f"/api/sheets/{P26}/quality", params=params)).json()
    unique = next(c for c in quality["checks"] if c["check"] == "unique")
    assert unique["issues"][0]["value"] == "10521"
    designers = (await client.get("/api/designers")).json()
    names = {d["name"]: d for d in designers["designers"]}
    assert names["Carla Ruiz"]["in_catalog"] is False
    assert names["Ana Pérez"]["person"]["email"] == "ana@example.com"
    assert designers["header_like_rows"] == 1
    export = (await client.get("/api/export/access.csv")).content.decode("utf-8-sig")
    assert len(list(csv.reader(io.StringIO(export), delimiter=";"))) > 10


async def test_writes_are_recorded_by_the_fake(stack) -> None:
    client, fake = stack
    body = {"recipients": [{"email": "nueva@example.com"}], "access_level": "VIEWER"}
    created = await client.post(f"/api/sheets/{P26}/shares", json=body)
    assert (
        created.status_code == 201 and created.json()["created"][0]["email"] == "nueva@example.com"
    )
    updated = await client.patch(
        f"/api/sheets/{P26}/shares/S-LUIS", json={"access_level": "EDITOR"}
    )
    assert updated.json()["access_level"] == "EDITOR"
    assert (await client.delete(f"/api/sheets/{P26}/shares/S-ANA")).status_code == 204
    assert [(w["method"], w["query"].get("sendEmail")) for w in fake.writes] == [
        ("POST", "false"),
        ("PATCH", None),
        ("DELETE", None),
    ]
    blocked = await client.delete(f"/api/sheets/{fake_data.FOREIGN}/shares/S-OTRA")
    assert blocked.json()["detail"]["code"] == "NOT_SHARED_WITH_TOKEN"
    assert len(fake.writes) == 3
