"""Barreras de simulación y comprobación del inventario sin llamadas externas."""

from dataclasses import replace
from unittest.mock import AsyncMock

import pytest

pytest.importorskip("psycopg")

from app.services.ids import EntityKind  # noqa: E402
from app.services.ids.dry_run import PILOT_WORKSPACE, Candidate, PlanAction, plan  # noqa: E402
from app.services.ids.inventory import InventorySheet, collect_inventory  # noqa: E402
from app.services.ids.pilot import SHEETS, read_pilot  # noqa: E402
from app.services.ids.simulation import Projector  # noqa: E402
from app.services.ids.transition import approved_starts  # noqa: E402
from app.services.smartsheet import RawColumn, RawRow  # noqa: E402


def test_simulation_refuses_untrusted_and_conflicting_data() -> None:
    candidate = Candidate(
        "1", PILOT_WORKSPACE, EntityKind.TASK, "KMV-BS-26-452", True, "KMV-BS-26-452-02", "", None
    )
    allowed = frozenset({"1"})
    assert plan(candidate, allowed) == PlanAction.NEEDS_RESERVATION
    assert plan(replace(candidate, workspace_id=None), allowed) == PlanAction.DENIED
    assert plan(candidate, frozenset()) == PlanAction.DENIED
    assert plan(replace(candidate, parent_confirmed=False), allowed) == PlanAction.PENDING_PARENT
    assert plan(replace(candidate, reserved_id="KMV-BS-26-452-03"), allowed) == PlanAction.CONFLICT
    assert (
        plan(replace(candidate, reserved_id=candidate.visible_id), allowed)
        == PlanAction.WOULD_WRITE
    )
    assert plan(replace(candidate, stable_id="other"), allowed) == PlanAction.CONFLICT
    assert (
        plan(replace(candidate, stable_id=candidate.visible_id), allowed)
        == PlanAction.ALREADY_STABLE
    )
    assert (
        plan(
            replace(
                candidate,
                stable_id=candidate.visible_id,
                reserved_id=candidate.visible_id,
                reserved_state="reservado",
            ),
            allowed,
        )
        == PlanAction.CONFIRM_RESERVATION
    )
    assert plan(replace(candidate, parent="KMV-CC-26-452"), allowed) == PlanAction.CONFLICT


def row(row_id: str, visible: str, stable: str) -> RawRow:
    return RawRow(row_id, None, None, None, None, None, None, {"v": visible, "s": stable})


def test_inventory_rejects_mismatch_and_duplicates() -> None:
    item = InventorySheet(
        1,
        EntityKind.PROJECT,
        "v",
        "s",
        [row("1", "KMV-BS-26-452", "KMV-BS-26-452"), row("2", "", "")],
    )
    assert len(collect_inventory([item])) == 1
    with pytest.raises(ValueError):
        collect_inventory([replace(item, rows=[row("1", "KMV-BS-26-452", "")])])
    with pytest.raises(ValueError):
        collect_inventory([item, item])


def test_inventory_requires_matching_parent_reference() -> None:
    project = InventorySheet(
        1, EntityKind.PROJECT, "v", "s", [row("1", "KMV-BS-26-452", "KMV-BS-26-452")]
    )
    task_row = replace(
        row("2", "KMV-BS-26-452-02", "KMV-BS-26-452-02"),
        cells={"v": "KMV-BS-26-452-02", "s": "KMV-BS-26-452-02", "p": "KMV-BS-26-452"},
    )
    task = InventorySheet(2, EntityKind.TASK, "v", "s", [task_row], "p")
    assert len(collect_inventory([project, task])) == 2
    with pytest.raises(ValueError):
        collect_inventory([task])


def test_hypothetical_ids_do_not_mutate_database_snapshot() -> None:
    scopes = {"task:KMV-BS-26-452": 2}
    used = {"KMV-BS-26-452-03"}
    projector = Projector(scopes, used)
    assert projector.next(EntityKind.TASK, "KMV-BS-26-452") == "KMV-BS-26-452-04"
    assert projector.next(EntityKind.TASK, "KMV-BS-26-452") == "KMV-BS-26-452-05"
    assert scopes["task:KMV-BS-26-452"] == 2
    with pytest.raises(ValueError):
        projector.next(EntityKind.PROJECT, "KMV-OT-26")


def test_transition_policy_requires_approval_and_valid_scope() -> None:
    raw = '{"task:KMV-BS-26-452": 90}'
    assert approved_starts(raw, approved=False) == {}
    assert approved_starts(raw, approved=True) == {"task:KMV-BS-26-452": 90}
    with pytest.raises(ValueError):
        approved_starts('{"task:invalido": 1}', approved=True)


async def test_pilot_rechecks_workspace_and_rejects_unknown() -> None:
    client = AsyncMock()
    client.sheet_workspace_id.return_value = PILOT_WORKSPACE
    client.sheet_version.return_value = 1
    titles = {
        name
        for _, _, visible, stable, parent in SHEETS
        for name in (visible, stable, parent)
        if name
    }
    titles.add("Reference")
    titles.update(("KMV/GALP", "Customer Code", "Date Received"))
    client.list_columns.return_value = [
        RawColumn(str(number), title, number, False) for number, title in enumerate(titles, 1)
    ]
    client.list_rows.return_value = []
    assert len(await read_pilot(client)) == 4
    client.sheet_workspace_id.return_value = None
    with pytest.raises(ValueError):
        await read_pilot(client)
