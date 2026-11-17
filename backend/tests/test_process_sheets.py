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
from app.services.childsheets.specs import DESIGN_TICKETS, INHERITED, MOT, PERMITS
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
        ({"Type of Project": "KMV-Miscellaneous"}, False, True),  # proyecto de permisos
    ],
)
def test_permit_rows_need_type_agency_and_an_open_status(values, child, expected) -> None:
    assert PERMITS.when(values, child) is expected


def test_mot_rows_are_mot_children_and_mothers_with_packages() -> None:
    assert MOT.when({"Type of Project": "KMV-MOT", "Agency": "FDOT"}, True)
    assert MOT.when({"Prepare Packages": True}, False)
    assert not MOT.when({"Prepare Packages": False}, False)
    assert not MOT.when({"Type of Project": "KMV-Permit", "Agency": "FDOT"}, True)


def test_a_permit_with_its_own_package_gets_a_package_row() -> None:
    """HP-18: paquete por permiso (en 2026, un proyecto con un paquete por permiso de edificio)."""
    own = {"Type of Project": "KMV-Permit", "Agency": "City", "Prepare Packages": True}
    assert MOT.when(own, True) and MOT.kind(own, True) == "Package"
    closed = {"Type of Project": "KMV-Line", "Project Status": "NO PERMIT REQUIRED"}
    assert MOT.when(closed | {"Prepare Packages": True}, True)
    assert MOT.kind({"Type of Project": "KMV-MOT", "Prepare Packages": True}, True) == "MOT"
    assert MOT.kind({"Type of Project": "KMV-P", "Prepare Packages": True}, False) == "Package"


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


async def test_misc_projects_go_to_permits_and_only_permit_data_returns(router) -> None:
    sheets = _sheets(router, PERMITS_MASTER, PERMITS_CHILD)
    mother = {"Tracking Project": "KMV-26-0001", "Type of Project": "KMV-Miscellaneous"}
    mother |= {"Project Status": "IN PERMITTING", "Linked Tracking": "KMV-CC-25-090"}
    child = {"Tracking Project": "KMV-26-0001", "Type of Project": "KMV-Permit", "Agency": "FDOT"}
    _family(sheets, {"1": mother, "2": child})
    settings = make_settings(**ON)
    client = SmartsheetClient(settings)
    sync = ChildSheetSync(settings, client, PERMITS, CHILD, interval=0)
    try:
        created = await sync.run()
        rows = {r["Master Row"]: r for r in sheets.rows[CHILD].values()}
        rows["1"].update({"Permit Status": "4. Permit Process", "Permit #": "M-1"})
        back = await sync.run()
    finally:
        await client.aclose()
    assert created["created"] == 2
    assert rows["2"]["Linked Tracking"] == "KMV-CC-25-090"  # del proyecto
    assert back["summarized"] == 1
    assert sheets.rows[M]["1"]["Permit #"] == "M-1"
    assert sheets.rows[M]["1"]["Project Status"] == "IN PERMITTING"  # lo lleva la coordinación


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


async def test_permit_package_row_never_overwrites_the_permit_status(router) -> None:
    sheets = _sheets(router, MOT_MASTER, MOT_CHILD)
    mother = {"Tracking Project": "KMV-26-0001", "Type of Project": "KMV-P"}
    permit = {"Tracking Project": "KMV-26-0001", "Type of Project": "KMV-Permit"}
    permit |= {"Agency": "City", "Prepare Packages": True, "Project Status": "4. Permit Process"}
    _family(sheets, {"1": mother | {"Project Name": "A"}, "2": permit})
    settings = make_settings(**WRITES | {"app_mot_sync_enabled": True, "app_mot_sheet_id": CHILD})
    client = SmartsheetClient(settings)
    sync = ChildSheetSync(settings, client, MOT, CHILD, interval=0)
    try:
        await sync.run()
        for row in sheets.rows[CHILD].values():
            row["MOT Status"] = "3. Packages Completed"
        back = await sync.run()
    finally:
        await client.aclose()
    rows = list(sheets.rows[CHILD].values())
    kinds = [(r["Master Row"], r["Row Type"], r["Agency"]) for r in rows]
    assert kinds == [("2", "Package", "City")]
    assert rows[0]["Project Name"] == "A"
    assert back["summarized"] == 0
    assert sheets.rows[M]["2"]["Project Status"] == "4. Permit Process"


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


DT_MASTER = [*DESIGN_TICKETS.context, "Design Ticket", "Mile Post"]
DT_CHILD = [*DESIGN_TICKETS.context, "Master Row", "Design Ticket", "Mile Post"]


async def test_design_tickets_are_filled_by_their_owner_and_go_back_to_the_project(
    router,
) -> None:
    sheets = _sheets(router, DT_MASTER, DT_CHILD)
    sheets.rows[M] = {
        "1": {"Tracking Project": "KMV-26-0001", "DT Owner": "persona1@example.com"},
        "2": {"Tracking Project": "KMV-26-0002"},
    }
    settings = make_settings(
        **WRITES | {"app_design_tickets_sync_enabled": True, "app_design_tickets_sheet_id": CHILD}
    )
    client = SmartsheetClient(settings)
    sync = ChildSheetSync(settings, client, DESIGN_TICKETS, CHILD, interval=0)
    try:
        created = await sync.run()
        (row,) = sheets.rows[CHILD].values()
        row.update({"Design Ticket": "261100789", "Mile Post": True})
        back = await sync.run()
    finally:
        await client.aclose()
    assert created["created"] == 1 and row["Master Row"] == "1"
    assert back["summarized"] == 1
    assert sheets.rows[M]["1"]["Design Ticket"] == "261100789"
    assert sheets.rows[M]["1"]["Mile Post"] is True


def test_hooks_run_inheritance_first_and_lists_last() -> None:
    everything = ON | {
        "app_inherit_enabled": True,
        "app_billing_sync_enabled": True,
        "app_billing_sheet_id": "888",
        "app_mot_sync_enabled": True,
        "app_mot_sheet_id": "999",
        "ids_project_options_enabled": True,
        "app_design_tickets_sync_enabled": True,
        "app_design_tickets_sheet_id": "555",
    }
    hooks = child_hooks(make_settings(**everything), None)
    expected = ["inherit", "records", "billing", "permits", "mot", "design_tickets", "options"]
    assert list(hooks) == expected
    assert child_hooks(make_settings(**everything | {"app_read_only": True}), None) == {}
