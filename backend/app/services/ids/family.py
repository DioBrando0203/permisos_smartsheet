"""Decisiones de familia en Presentable: madre con otro cliente e hijas (SPEC-ID01 ID-38, ID-44+).

Funciones puras sobre el inventario leído; no reservan, consultan ni escriben.
"""

from collections import Counter

from app.services.ids.dry_run import PlanAction
from app.services.ids.formats import EntityKind, customer_code, parse_id
from app.services.ids.inventory import InventorySheet

# `Type of Project` de un permiso; `KMV-P` y `KMV-Miscellaneous` son el proyecto (ID-51).
PERMIT_TYPES = frozenset({"KMV-Permit", "KMV-Line", "KMV-MOT"})


def children_plan(
    sheet: InventorySheet, confirmed: set[str], counts: Counter, details: list, change: bool
) -> None:
    """Filas hijas: llevan el ID de su madre; se completan sólo con la madre confirmada."""
    mothers = {row.id: (row.cells.get(sheet.stable_column) or "").strip() for row in sheet.rows}
    code = sheet.project_columns[1] if sheet.project_columns else None
    codes = {row.id: (row.cells.get(code) or "").strip() for row in sheet.rows} if code else {}
    for child, root in sheet.children:
        stable = (child.cells.get(sheet.stable_column) or "").strip()
        mother = mothers.get(root, "")
        mine = (child.cells.get(code) or "").strip() if code else ""
        action = _child_action(
            change, stable, mother, mine, codes.get(root, ""), mother in confirmed
        )
        if action is None:
            counts["child_inherited"] += 1
            continue
        counts[action.value] += 1
        details.append(
            {
                "sheet_id": str(sheet.sheet_id),
                "row_id": str(child.id),
                "type": sheet.kind.value,
                "parent": mother or (str(root) if action == PlanAction.DETACH_CHILD else ""),
                "action": action.value,
                "visible_id": (child.cells.get(sheet.visible_column) or "").strip(),
                "stable_id": stable,
                "proposed_id": mother if action == PlanAction.CHILD_FILL else None,
                "mother_row_id": root,
                "renumbered": False,
            }
            | ({"replace": True} if action == PlanAction.CHILD_FILL and stable else {})
        )


def _child_action(
    change: bool, stable: str, mother: str, mine: str, theirs: str, confirmed: bool
) -> PlanAction | None:
    """None si la hija ya lleva el ID de su madre.

    Con `change` (ID-44 a ID-47): espera mientras la madre cambia de cliente; sigue a la madre si
    conserva su cliente e ID anteriores; sale de la jerarquía si su cliente cambió; y una hija
    con otro ID (copiada) toma el de su madre.
    """
    if change and theirs and _customer_of(mother) not in ("", theirs):
        return PlanAction.PENDING_PARENT
    if change and mine and theirs and mine != theirs:
        if stable and stable != mother and _customer_of(stable) == mine:
            return PlanAction.CHILD_FOLLOW if confirmed else PlanAction.PENDING_PARENT
        return PlanAction.DETACH_CHILD
    if mother and stable == mother:
        return None
    if not mother:
        return PlanAction.PENDING_PARENT
    if stable and not (change and confirmed):
        return PlanAction.CONFLICT  # la hija dice pertenecer a otro proyecto
    return PlanAction.CHILD_FILL if confirmed else PlanAction.PENDING_PARENT


def _customer_of(value: str) -> str:
    try:
        return customer_code(parse_id(EntityKind.PROJECT, value).parent) if value else ""
    except ValueError:
        return ""


def adoptions(sheet: InventorySheet) -> dict[str, str]:
    """Permiso de primer nivel -> madre de tipo proyecto cuyo Stable ID es su `Parent Project`.

    ID-51: la madre debe ser única y del mismo `Customer Code` (o la fila sin cliente propio).
    """
    if not sheet.adopt_columns:
        return {}
    kind, linked = sheet.adopt_columns
    code = sheet.project_columns[1] if sheet.project_columns else None
    owners: dict[str, list] = {}
    for row in sheet.rows:
        stable = (row.cells.get(sheet.stable_column) or "").strip()
        if stable and (row.cells.get(kind) or "").strip() not in PERMIT_TYPES:
            owners.setdefault(stable, []).append(row)
    found = {}
    for row in sheet.rows:
        target = (row.cells.get(linked) or "").strip()
        mothers = owners.get(target, [])
        if (row.cells.get(kind) or "").strip() not in PERMIT_TYPES or len(mothers) != 1:
            continue
        mine = (row.cells.get(code) or "").strip() if code else ""
        theirs = (mothers[0].cells.get(code) or "").strip() if code else ""
        if mothers[0].id != row.id and (not mine or mine == theirs):
            found[row.id] = mothers[0].id
    return found


def customer_changed(kind: EntityKind, stable: str, parent: str) -> bool:
    """Madre cuyo Stable ID es de otro cliente que el de sus datos actuales (ID-44)."""
    if kind != EntityKind.PROJECT or not stable or not parent:
        return False
    try:
        old = customer_code(parse_id(kind, stable).parent)
    except ValueError:
        return False
    return bool(old) and old != customer_code(parent)
