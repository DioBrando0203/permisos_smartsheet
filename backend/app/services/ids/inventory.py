"""Construcción del inventario comprobado; no modifica bases ni hojas."""

from dataclasses import dataclass

from app.services.ids.formats import EntityKind, parse_id
from app.services.ids.store import ExistingId
from app.services.smartsheet import RawRow


@dataclass(frozen=True)
class InventorySheet:
    sheet_id: int
    kind: EntityKind
    visible_column: str
    stable_column: str
    rows: list[RawRow]
    parent_column: str | None = None
    extra_parent_column: str | None = None
    # (empresa o None, cliente, fecha); sin columna de empresa se usa la de la fórmula.
    project_columns: tuple[str | None, str, str] | None = None
    # Filas hijas y la fila de primer nivel de la que heredan el ID (Presentable).
    children: tuple[tuple[RawRow, str], ...] = ()
    # `Type of Project` y `Linked Tracking`, si la hoja los tiene: permisos sueltos (ID-51).
    adopt_columns: tuple[str, str] | None = None


def collect_inventory(
    sheets: list[InventorySheet], *, ignore_pending: bool = False
) -> list[ExistingId]:
    """Rechaza IDs parciales, diferentes o repetidos antes de cualquier importación."""
    entries: list[ExistingId] = []
    seen_values: set[str] = set()
    seen_rows: set[tuple[int, int]] = set()
    for sheet in sheets:
        for row in sheet.rows:
            visible = (row.cells.get(sheet.visible_column) or "").strip()
            stable = (row.cells.get(sheet.stable_column) or "").strip()
            if not visible and not stable:
                continue
            if ignore_pending and visible and not stable:
                continue
            if not visible or visible != stable:
                raise ValueError("ID visible y estable ausentes o distintos")
            parse_id(sheet.kind, stable)
            key = (sheet.sheet_id, int(row.id))
            if stable in seen_values or key in seen_rows:
                raise ValueError("ID o fila duplicada en inventario")
            seen_values.add(stable)
            seen_rows.add(key)
            entries.append(ExistingId(sheet.sheet_id, key[1], sheet.kind, stable))
    if not entries:
        raise ValueError("Inventario vacío")
    _validate_parents(sheets, entries)
    return entries


def _validate_parents(sheets: list[InventorySheet], entries: list[ExistingId]) -> None:
    values = {entry.value for entry in entries}
    for sheet in sheets:
        if sheet.kind == EntityKind.PROJECT:
            continue
        if not sheet.parent_column:
            raise ValueError("Falta columna de referencia al padre")
        for row in sheet.rows:
            stable = (row.cells.get(sheet.stable_column) or "").strip()
            if not stable:
                continue
            parent = parse_id(sheet.kind, stable).parent
            reference = (row.cells.get(sheet.parent_column) or "").strip()
            if reference != parent or parent not in values:
                raise ValueError("Referencia al padre ausente o inconsistente")
            if sheet.extra_parent_column:
                extra = (row.cells.get(sheet.extra_parent_column) or "").strip()
                if extra != parent:
                    raise ValueError("Referencia adicional al padre inconsistente")
