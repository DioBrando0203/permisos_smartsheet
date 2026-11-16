"""Hojas de proceso, herencia y listas de proyectos (SPEC-B20, SPEC-ID01 ID-55, PEN-54).

Smartsheet simulado y datos sintéticos; ninguna solicitud sale a Smartsheet.
"""

import json
import re

import httpx
import pytest
import respx

from app.services.childsheets.inherit import InheritSync
from app.services.childsheets.options import ProjectOptions
from app.services.childsheets.specs import INHERITED, MOT, PERMITS
from app.services.childsheets.sync import ChildSheetSync, child_hooks
from app.services.ids import pilot
from app.services.ids.dry_run import PILOT_WORKSPACE
from app.services.smartsheet import SmartsheetClient
from tests.conftest import BASE, make_settings
from tests.test_childsheets import CHILD, WRITES, _sheets

M = pilot.PRESENTABLE
BACK = ["Project Status", "Permit #", "Permit Approved", "Permit Expires", "Permit Fee"]
PERMITS_MASTER = [*PERMITS.context, "Project Status", "LT", *BACK[1:]]
PERMITS_CHILD = [*PERMITS.context, "Master Row", "LT", "Permit Status", *BACK[1:]]
ON = WRITES | {"app_permits_sync_enabled": True, "app_permits_sheet_id": CHILD}


@pytest.fixture
def router():
    with respx.mock(assert_all_called=False) as mock:
        yield mock


@pytest.mark.parametrize(
    ("values", "child", "expected"),
    [
        ({"Type of Project": "KMV-Permit", "Agency": "FDOT"}, True, True),
        ({"Type of Project": "KMV-Line", "Agency": "Miami"}, True, True),
        ({"Type of Project": "KMV-Line"}, True, False),  # sin agencia
        (
            {
                "Type of Project": "KMV-Line",
                "Agency": "FDOT",
                "Project Status": "NO PERMIT REQUIRED",
            },
            True,
            False,
        ),
        (
            {"Type of Project": "KMV-Permit", "Agency": "FDOT", "Project Status": "CANCELLED"},
            True,
            False,
        ),
        ({"Type of Project": "KMV-MOT", "Agency": "FDOT"}, True, False),  # va a MOT & Packages
        ({"Type of Project": "KMV-P", "Agency": "FDOT"}, False, False),  # madre
    ],
)
def test_permit_rows_need_type_agency_and_an_open_status(values, child, expected) -> None:
    assert PERMITS.when(values, child) is expected


def test_mot_rows_are_mot_children_and_mothers_with_packages() -> None:
    assert MOT.when({"Type of Project": "KMV-MOT", "Agency": "FDOT"}, True)
    assert MOT.when({"Prepare Packages": True}, False)
    assert not MOT.when({"Prepare Packages": False}, False)
    assert not MOT.when({"Type of Project": "KMV-Permit", "Agency": "FDOT"}, True)


def _family(sheets, rows: dict[str, dict], mother: str = "1") -> None:
    sheets.rows[M] = rows
    sheets.parents.update({row: mother for row in rows if row != mother})


async def test_permits_take_project_data_return_status_and_follow_cancellation(router) -> None:
    sheets = _sheets(router, PERMITS_MASTER, PERMITS_CHILD)
    mother = {"Tracking Project": "KMV-26-0001", "Type of Project": "KMV-P", "Project Name": "A"}
    mother |= {"Permitting Team": "persona1@example.com", "Project Status": "IN PERMITTING"}
    child = {"Tracking Project": "KMV-26-0001", "Type of Project": "KMV-Permit"}
    _family(
        sheets,
        {
            "1": mother,
            "2": child | {"Agency": "FDOT", "LT": "2026-11-02"},
            "3": child | {"Type of Project": "KMV-Line"},  # sin agencia todavía
            "4": child | {"Agency": "Miami", "Project Status": "NO PERMIT REQUIRED"},
        },
    )
    settings = make_settings(**ON)
    client = SmartsheetClient(settings)
    sync = ChildSheetSync(settings, client, PERMITS, CHILD, interval=0)
    try:
        first = await sync.run()
        (row,) = sheets.rows[CHILD].values()
        row.update({"Permit Status": "4. Permit Process", "Permit #": "P-1"})
        sheets.rows[M]["3"]["Agency"] = "Doral"
        second = await sync.run()
        sheets.rows[M]["2"]["Project Status"] = "CANCELLED"
        third = await sync.run()
    finally:
        await client.aclose()
    assert first["created"] == 1 and first["summarized"] == 0
    assert (row["Master Row"], row["Project Name"], row["LT"]) == ("2", "A", "2026-11-02")
    assert row["Permitting Team"] == "persona1@example.com"  # de su proyecto
    assert second["created"] == 1 and second["summarized"] == 1
    assert sheets.rows[M]["2"]["Project Status"] == "CANCELLED"
    assert sheets.rows[M]["2"]["Permit #"] == "P-1"
    assert sheets.rows[M]["1"]["Project Status"] == "IN PERMITTING"
    assert third["updated"] >= 1 and row["Permit Status"] == "CANCELLED"
    assert {r["Master Row"] for r in sheets.rows[CHILD].values()} == {"2", "3"}


MOT_MASTER = [*MOT.context, "Type of Project", "Project Status", "Prepare Packages", "LT"]
MOT_MASTER += ["Custom MOT", "TYPICAL MOT"]
MOT_CHILD = [*MOT.context, "Row Type", "Master Row", "LT", "MOT Status", "Custom MOT"]


async def test_mot_rows_for_mot_children_and_packages_status_only_for_children(router) -> None:
    sheets = _sheets(router, MOT_MASTER, MOT_CHILD)
    _family(
        sheets,
        {
            "1": {
                "Tracking Project": "KMV-26-0001",
                "Type of Project": "KMV-P",
                "Project Status": "IN PERMITTING",
                "Prepare Packages": True,
                "Customer": "CC-Crown Castle",
            },
            "2": {
                "Tracking Project": "KMV-26-0001",
                "Type of Project": "KMV-MOT",
                "Agency": "FDOT",
            },
        },
    )
    settings = make_settings(**WRITES | {"app_mot_sync_enabled": True, "app_mot_sheet_id": CHILD})
    client = SmartsheetClient(settings)
    sync = ChildSheetSync(settings, client, MOT, CHILD, interval=0)
    try:
        await sync.run()
        for row in sheets.rows[CHILD].values():
            row["MOT Status"] = "5. Design MOT Process"
            row["Custom MOT"] = "1"
        back = await sync.run()
    finally:
        await client.aclose()
    kinds = sorted((r["Master Row"], r["Row Type"]) for r in sheets.rows[CHILD].values())
    assert kinds == [("1", "Package"), ("2", "MOT")]
    mot = next(r for r in sheets.rows[CHILD].values() if r["Master Row"] == "2")
    assert mot["Customer"] == "CC-Crown Castle"
    assert back["summarized"] == 1
    assert sheets.rows[M]["2"]["Project Status"] == "5. Design MOT Process"
    assert sheets.rows[M]["1"]["Project Status"] == "IN PERMITTING"


async def test_children_inherit_only_empty_project_cells(router) -> None:
    sheets = _sheets(router, ["Tracking Project", *INHERITED], ["Master Row"])
    mother = {"Tracking Project": "KMV-26-0001", "Project Name": "A", "City": "Doral"}
    mother |= {"Customer": "CC-Crown Castle", "LT": "2026-11-02"}
    _family(sheets, {"1": mother, "2": {"City": "Miami"}, "3": {}})
    settings = make_settings(**WRITES | {"app_inherit_enabled": True})
    client = SmartsheetClient(settings)
    sync = InheritSync(settings, client, interval=0)
    try:
        first = await sync.run()
        second = await sync.run()
    finally:
        await client.aclose()
    assert first == {"filled": 2, "deferred": 0} and second["filled"] == 0
    assert sheets.rows[M]["2"] == {
        "City": "Miami",
        "Project Name": "A",
        "Customer": "CC-Crown Castle",
        "LT": "2026-11-02",
    }
    assert sheets.rows[M]["3"]["City"] == "Doral"


class Options:
    """Maestra con `Parent Project` y `Linked Tracking` como desplegables; registra cambios."""

    def __init__(self, rows: list[dict]) -> None:
        self.rows = rows
        self.options = {"Parent Project": [], "Linked Tracking": ["KMV-CC-25-090"]}
        self.puts: list[tuple[int, dict]] = []

    def handle(self, request: httpx.Request) -> httpx.Response:
        path = request.url.path
        titles = ["Type of Project", "Stable Tracking Project", *self.options]
        if request.method == "PUT":
            column = int(re.search(r"/columns/(\d+)", path).group(1))
            body = json.loads(request.content)
            self.puts.append((column, body))
            self.options[titles[column - 1]] = body["options"]
            return httpx.Response(200, json={"message": "SUCCESS"})
        if path.endswith("/columns"):
            data = [
                {
                    "id": i + 1,
                    "title": t,
                    "index": i,
                    "type": "PICKLIST" if i > 1 else "TEXT_NUMBER",
                }
                | ({"options": self.options[t]} if i > 1 else {})
                for i, t in enumerate(titles)
            ]
            return httpx.Response(200, json={"data": data, "pageNumber": 1, "totalPages": 1})
        rows = [
            {
                "id": i + 1,
                "cells": [{"columnId": 1, "value": r["type"]}, {"columnId": 2, "value": r["id"]}],
            }
            | ({"parentId": r["parent"]} if r.get("parent") else {})
            for i, r in enumerate(self.rows)
        ]
        workspace = {"id": int(PILOT_WORKSPACE)}
        return httpx.Response(200, json={"id": 1, "workspace": workspace, "rows": rows})


async def test_project_lists_follow_the_projects() -> None:
    fake = Options(
        [
            {"type": "KMV-P", "id": "KMV-26-0001"},
            {"type": "KMV-Miscellaneous", "id": "KMV-26-0002"},
            {"type": "KMV-Permit", "id": "KMV-26-0001", "parent": 1},
            {"type": "KMV-Permit", "id": "KMV-26-0003"},  # permiso suelto: no es proyecto
            {"type": "KMV-P", "id": "Pending ID"},
        ]
    )
    settings = make_settings(**WRITES | {"ids_project_options_enabled": True})
    client = SmartsheetClient(settings)
    try:
        with respx.mock(assert_all_called=False) as mock:
            mock.route(url__startswith=f"{BASE}/sheets/").mock(side_effect=fake.handle)
            first = await ProjectOptions(settings, client, interval=0).run()
            second = await ProjectOptions(settings, client, interval=0).run()
    finally:
        await client.aclose()
    assert first == {"updated": 2, "projects": 2} and second["updated"] == 0
    assert fake.options["Parent Project"] == ["KMV-26-0002", "KMV-26-0001"]
    assert fake.options["Linked Tracking"] == ["KMV-CC-25-090", "KMV-26-0002", "KMV-26-0001"]


def test_hooks_run_inheritance_first_and_lists_last() -> None:
    everything = ON | {
        "app_inherit_enabled": True,
        "app_billing_sync_enabled": True,
        "app_billing_sheet_id": "888",
        "app_mot_sync_enabled": True,
        "app_mot_sheet_id": "999",
        "ids_project_options_enabled": True,
    }
    hooks = child_hooks(make_settings(**everything), None)
    assert list(hooks) == ["inherit", "records", "billing", "permits", "mot", "options"]
    assert child_hooks(make_settings(**everything | {"app_read_only": True}), None) == {}
