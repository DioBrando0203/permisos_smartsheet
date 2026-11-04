"""Adaptador de Smartsheet: validación y barreras usando clientes simulados."""

from datetime import date
from unittest.mock import AsyncMock, Mock

import pytest

from app.core.errors import AppError
from app.services.ids import manual
from app.services.ids.connector import Snapshot, Target
from app.services.ids.dry_run import PILOT_WORKSPACE
from app.services.ids.formats import EntityKind
from app.services.ids.gateway import SmartsheetIdGateway
from app.services.smartsheet import RawColumn, RawRow, SmartsheetClient
from tests.conftest import make_settings
from tests.factories import sheet_json


async def test_gateway_reads_parent_and_rechecks_before_write() -> None:
    client = AsyncMock()
    client.sheet_workspace_id.return_value = PILOT_WORKSPACE
    client.list_columns.side_effect = [
        [
            RawColumn("1", "Task ID", 0, True),
            RawColumn("2", "Stable Task ID", 1, False),
            RawColumn("3", "Tracking Project", 2, False),
            RawColumn("4", "Reference", 3, False),
        ],
        [RawColumn("5", "Stable Tracking Project", 0, True)],
    ] * 2
    parent = "KMV-BS-26-452"
    task = f"{parent}-03"
    client.get_row.side_effect = [
        RawRow(
            "2", 1, None, None, None, None, None, {"1": task, "2": "", "3": parent, "4": parent}
        ),
        RawRow("1", 1, None, None, None, None, None, {"5": parent}),
    ] * 2
    store = Mock()
    store.confirmed_parent.return_value = 1
    gateway = SmartsheetIdGateway(client, store)
    target = Target(73093952524164, 2, EntityKind.TASK, parent)
    snapshot = await gateway.read(target)
    assert snapshot == Snapshot(PILOT_WORKSPACE, parent, True, task, "")
    assert await gateway.write_if_unchanged(target, snapshot, task) is True
    client.update_stable_id_once.assert_awaited_once()


async def test_client_blocks_all_writes_in_read_only(smartsheet) -> None:
    client = SmartsheetClient(
        make_settings(app_read_only=True, ids_writes_enabled=True, ids_transition_approved=True)
    )
    try:
        with pytest.raises(AppError) as error:
            await client.update_stable_id_once("73093952524164", "1", "ID")
        assert error.value.code == "IDS_WRITE_BLOCKED"
        assert not smartsheet.calls
    finally:
        await client.aclose()


async def test_manual_execution_is_blocked_by_default(monkeypatch) -> None:
    monkeypatch.setattr(manual, "Settings", lambda: make_settings(app_read_only=True))
    with pytest.raises(ValueError, match="deshabilitada"):
        await manual.execute(73093952524164, 123, "KMV-BS-26-452", True)


async def test_manual_execution_requires_explicit_authorization(monkeypatch) -> None:
    # Sin OAuth por decisión del usuario, pero la bandera expresa sigue siendo obligatoria.
    monkeypatch.setattr(
        manual,
        "Settings",
        lambda: make_settings(
            app_read_only=False, ids_writes_enabled=True, ids_transition_approved=True
        ),
    )
    client = Mock()
    monkeypatch.setattr(manual, "SmartsheetClient", client)
    with pytest.raises(ValueError, match="no autorizada"):
        await manual.execute(73093952524164, 123, "KMV-BS-26-452", False)
    client.assert_not_called()


async def test_project_requires_company_customer_and_year() -> None:
    client = AsyncMock()
    client.sheet_workspace_id.return_value = PILOT_WORKSPACE
    client.list_columns.return_value = [
        RawColumn("1", "Tracking Project", 0, True),
        RawColumn("2", "Stable Tracking Project", 1, False),
        RawColumn("3", "KMV/GALP", 2, False),
        RawColumn("4", "Customer Code", 3, False),
        RawColumn("5", "Year", 4, False),
        RawColumn("6", "Date Received", 5, False),
    ]
    client.get_row.return_value = RawRow(
        "2",
        1,
        None,
        None,
        None,
        None,
        None,
        {"3": "KMV", "4": "BS", "5": "2099", "6": "03/02/2026"},
        {"6": date(2026, 3, 2)},
    )
    gateway = SmartsheetIdGateway(client, Mock())
    target = Target(4365321059389316, 2, EntityKind.PROJECT, "KMV-BS-26")
    assert (await gateway.read(target)).parent == "KMV-BS-26"
    client.get_row.return_value.cells["4"] = ""
    assert (await gateway.read(target)).parent == ""


def test_raw_date_uses_iso_value_not_localized_display() -> None:
    from app.services.smartsheet.mappers import to_row

    result = to_row(
        {"id": 1, "cells": [{"columnId": 6, "value": "2027-02-03", "displayValue": "03/02/2027"}]}
    )
    assert result.cells["6"] == "03/02/2027"
    assert result.date_cells["6"] == date(2027, 2, 3)


async def test_client_checks_workspace_and_empty_stable_before_mock_write(smartsheet) -> None:
    sheet = "73093952524164"
    smartsheet.get(f"/sheets/{sheet}").respond(
        json=sheet_json(sheet) | {"workspace": {"id": int(PILOT_WORKSPACE)}, "accessLevel": "ADMIN"}
    )
    smartsheet.get(f"/sheets/{sheet}/columns").respond(
        json={
            "data": [{"id": 11, "title": "Stable Task ID", "index": 0, "primary": True}],
            "totalPages": 1,
        }
    )
    row = smartsheet.get(f"/sheets/{sheet}/rows/2")
    row.respond(json={"id": 2, "rowNumber": 1, "cells": [{"columnId": 11, "value": None}]})
    put = smartsheet.put(f"/sheets/{sheet}/rows").respond(json={"message": "SUCCESS"})
    client = SmartsheetClient(
        make_settings(app_read_only=False, ids_writes_enabled=True, ids_transition_approved=True)
    )
    try:
        await client.update_stable_id_once(sheet, "2", "KMV-BS-26-452-03")
        assert put.call_count == 1
        row.respond(
            json={"id": 2, "rowNumber": 1, "cells": [{"columnId": 11, "value": "existente"}]}
        )
        with pytest.raises(AppError) as error:
            await client.update_stable_id_once(sheet, "2", "KMV-BS-26-452-04")
        assert error.value.code == "IDS_STABLE_EXISTS"
        assert put.call_count == 1
    finally:
        await client.aclose()
