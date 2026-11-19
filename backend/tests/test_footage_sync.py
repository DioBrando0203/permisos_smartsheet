"""Metraje en la maestra y en `Billing`, con aviso por correo (SPEC-B19 FH-05c).

Smartsheet simulado y datos sintéticos; ninguna solicitud sale a Smartsheet.
"""

import json
import re
from datetime import UTC, datetime

import httpx
import respx

from app.services.childsheets.footage import Change, FootageSync, billing_wins, notice
from app.services.childsheets.specs import FOOTAGE
from app.services.childsheets.sync import billing_spec, child_hooks
from app.services.ids import pilot
from app.services.ids.dry_run import PILOT_WORKSPACE
from app.services.smartsheet import SmartsheetClient
from tests.conftest import BASE, make_settings
from tests.test_childsheets import WRITES

BILLING, DIRECTORY = "888", "444"
ON = WRITES | {
    "app_billing_sync_enabled": True,
    "app_billing_sheet_id": BILLING,
    "app_footage_sync_enabled": True,
    "app_contacts_sheet_id": DIRECTORY,
}
MASTER_COLS = ("Tracking Project", "Project Name", *FOOTAGE)  # ids 1 a 7
BILLING_COLS = ("Master Row", "Tracking Project", "Project Name", *FOOTAGE)  # ids 11 a 18
DIRECTORY_COLS = (("Name", "TEXT_NUMBER"), ("Email", "CONTACT_LIST"))
DIRECTORY_COLS += (("Teams", "MULTI_PICKLIST"), ("Active", "CHECKBOX"))  # ids 21 a 24


def at(hour: int) -> str:
    return f"2026-11-19T{hour:02d}:00:00Z"


def test_the_sheet_changed_last_wins() -> None:
    early, late = datetime(2026, 11, 19, 9, tzinfo=UTC), datetime(2026, 11, 19, 11, tzinfo=UTC)
    assert billing_wins(early, late) and not billing_wins(late, early)
    assert billing_wins(None, early) and not billing_wins(early, None)
    subject, message = notice(
        "KMV-26-0001", "A", [Change("UG", "100", "120"), Change("ISP", None, "5")]
    )
    assert subject == "Footage updated in Billing: KMV-26-0001 – A"
    assert "UG: 100 → 120" in message and "ISP: (blank) → 5" in message


class Sheets:
    """Maestra, `Billing` y `Contact List`; registra escrituras, correos e historiales leídos."""

    def __init__(self, master: dict, billing: dict, history: dict, people: list) -> None:
        self.master, self.billing, self.history, self.people = master, billing, history, people
        self.puts: dict[str, list] = {}
        self.emails: list[dict] = []
        self.asked: list[tuple[int, int]] = []

    def handle(self, request: httpx.Request) -> httpx.Response:
        path = request.url.path
        sheet = re.search(r"/sheets/(\d+)", path).group(1)
        if request.method == "PUT":
            self.puts.setdefault(sheet, []).extend(json.loads(request.content))
            return httpx.Response(200, json={"message": "SUCCESS", "result": []})
        if request.method == "POST":
            self.emails.append(json.loads(request.content))
            return httpx.Response(200, json={"message": "SUCCESS"})
        if found := re.search(r"/rows/(\d+)/columns/(\d+)/history", path):
            key = (int(found.group(1)), int(found.group(2)))
            self.asked.append(key)
            data = [{"columnId": key[1], "modifiedAt": self.history[key], "value": "x"}]
            return httpx.Response(200, json={"data": data, "pageNumber": 1, "totalPages": 1})
        if path.endswith("/columns"):
            return self._page(self._columns(sheet))
        workspace = {"id": int(PILOT_WORKSPACE)}
        return httpx.Response(
            200, json={"id": int(sheet), "workspace": workspace, "rows": self._rows(sheet)}
        )

    def _page(self, data: list) -> httpx.Response:
        return httpx.Response(200, json={"data": data, "pageNumber": 1, "totalPages": 1})

    def _columns(self, sheet: str) -> list[dict]:
        if sheet == DIRECTORY:
            pairs = DIRECTORY_COLS
            start = 21
        else:
            pairs = [
                (t, "TEXT_NUMBER") for t in (BILLING_COLS if sheet == BILLING else MASTER_COLS)
            ]
            start = 11 if sheet == BILLING else 1
        return [
            {"id": start + i, "title": t, "index": i, "type": k} for i, (t, k) in enumerate(pairs)
        ]

    def _rows(self, sheet: str) -> list[dict]:
        if sheet == DIRECTORY:
            return [self._person(i, *p) for i, p in enumerate(self.people)]
        rows, titles, start = (
            (self.billing, BILLING_COLS, 11) if sheet == BILLING else (self.master, MASTER_COLS, 1)
        )
        return [
            {
                "id": int(row_id),
                "cells": [
                    {"columnId": start + i, "value": values[t], "displayValue": values[t]}
                    for i, t in enumerate(titles)
                    if values.get(t)
                ],
            }
            for row_id, values in rows.items()
        ]

    def _person(self, i: int, name: str, email: str, teams: str, active: bool) -> dict:
        cells = [
            {"columnId": 21, "value": name},
            {
                "columnId": 22,
                "value": email,
                "objectValue": {"objectType": "CONTACT", "email": email},
            },
            {"columnId": 23, "value": teams, "displayValue": teams},
            {"columnId": 24, "value": active},
        ]
        return {"id": 900 + i, "cells": cells}


def _sheets() -> Sheets:
    master = {"1": {"Tracking Project": "KMV-26-0001", "Project Name": "A"}}
    master["1"] |= {"Total Footage": "300", "UG": "100", "Aerial": "50"}
    billing = {"101": {"Master Row": "1", "Total Footage": "250", "UG": "120"}}
    # UG: Billing cambió después (gana Billing); Total Footage: la maestra cambió después.
    history = {(1, 4): at(10), (101, 15): at(11), (1, 3): at(12), (101, 14): at(9)}
    people = [
        ("Persona Uno", "persona1@example.com", "Design, Footage Alerts", True),
        ("Persona Dos", "persona2@example.com", "Footage Alerts", False),
    ]
    return Sheets(master, billing, history, people)


async def _run(fake: Sheets, settings) -> dict:
    client = SmartsheetClient(settings)
    try:
        with respx.mock(assert_all_called=False) as mock:
            mock.route(url__startswith=f"{BASE}/sheets/").mock(side_effect=fake.handle)
            return await FootageSync(settings, client, interval=0).run()
    finally:
        await client.aclose()


async def test_billing_corrections_reach_the_master_with_a_before_and_after_email() -> None:
    fake = _sheets()
    result = await _run(fake, make_settings(**ON))
    assert result == {"to_master": 1, "to_billing": 1, "notified": 1, "deferred": 0}
    assert fake.puts[pilot.PRESENTABLE] == [{"id": 1, "cells": [{"columnId": 4, "value": "120"}]}]
    (billing_row,) = fake.puts[BILLING]
    assert billing_row["id"] == 101
    assert {c["columnId"]: c["value"] for c in billing_row["cells"]} == {14: "300", 18: "50"}
    (email,) = fake.emails
    assert email["sendTo"] == [{"email": "persona1@example.com"}] and email["rowIds"] == [101]
    assert "UG: 100 → 120" in email["message"] and "Total Footage" not in email["message"]
    # Con Billing vacío gana la maestra sin consultar el historial (Aerial: columnas 7 y 18).
    assert sorted(fake.asked) == [(1, 3), (1, 4), (101, 14), (101, 15)]


async def test_without_directory_the_change_still_reaches_the_master() -> None:
    fake = _sheets()
    result = await _run(fake, make_settings(**ON | {"app_contacts_sheet_id": ""}))
    assert result["to_master"] == 1 and result["notified"] == 0 and not fake.emails


def test_billing_stops_copying_footage_only_with_the_footage_step() -> None:
    assert set(FOOTAGE) <= set(billing_spec(make_settings(**WRITES)).context)
    assert not set(FOOTAGE) & set(billing_spec(make_settings(**ON)).context)
    hooks = list(child_hooks(make_settings(**ON), None))
    assert hooks.index("footage") == hooks.index("billing") + 1
    assert "footage" not in child_hooks(
        make_settings(**ON | {"app_footage_sync_enabled": False}), None
    )
