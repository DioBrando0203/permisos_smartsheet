"""Hojas del ID Manager y su lectura: workspace comprobado en vivo, sin caché ni escrituras."""

from app.services.ids.dry_run import PILOT_WORKSPACE
from app.services.ids.formats import EntityKind
from app.services.ids.inventory import InventorySheet
from app.services.smartsheet import RawRow, SmartsheetClient

# Presentable (Pruebas), desde 2026-11-10: cada fila madre es un proyecto y sus filas hijas
# llevan el mismo ID. Se identifica por ID: renombrarla o moverla de carpeta no la afecta.
PRESENTABLE = "5254686035890052"
# Sin columna de empresa, la fórmula de Tracking Project fija "KMV".
DEFAULT_COMPANY = "KMV"
SHEETS = ((PRESENTABLE, EntityKind.PROJECT, "Tracking Project", "Stable Tracking Project", None),)
_PARENT_KIND = {
    EntityKind.TASK: EntityKind.PROJECT,
    EntityKind.RECORD: EntityKind.TASK,
    EntityKind.REVISION: EntityKind.TASK,
}


def sheet_spec(sheet_id: int | str) -> tuple | None:
    """Configuración de una hoja autorizada; se consulta en cada llamada."""
    return next((item for item in SHEETS if item[0] == str(sheet_id)), None)


def parent_spec(kind: EntityKind) -> tuple | None:
    """Hoja donde vive el padre de un tipo (proyecto de una tarea, tarea de un Record)."""
    wanted = _PARENT_KIND.get(kind)
    return next((item for item in SHEETS if item[1] == wanted), None)


def project_sheet() -> str:
    return next(item[0] for item in SHEETS if item[1] == EntityKind.PROJECT)


def split_hierarchy(rows: list[RawRow]) -> tuple[list[RawRow], list[tuple[RawRow, str]]]:
    """Filas de primer nivel y cada hija con la fila de primer nivel de la que hereda el ID."""
    parents = {row.id: row.parent_id for row in rows}
    top = [row for row in rows if not row.parent_id]
    children = []
    for row in rows:
        if not row.parent_id:
            continue
        root, seen = row.parent_id, set()
        while parents.get(root) and root not in seen:
            seen.add(root)
            root = parents[root]
        children.append((row, root))
    return top, children


async def read_pilot(client: SmartsheetClient) -> list[InventorySheet]:
    """Exige pertenencia actual y columnas exactas; detecta cambios durante la lectura."""
    result = []
    versions: dict[str, int] = {}
    for sheet_id, kind, visible, stable, parent in SHEETS:
        if await client.sheet_workspace_id(sheet_id) != PILOT_WORKSPACE:
            raise ValueError("Hoja fuera del workspace autorizado o workspace desconocido")
        versions[sheet_id] = await client.sheet_version(sheet_id)
        columns = await client.list_columns(sheet_id)
        extra_parent = "Reference" if kind == EntityKind.TASK else None
        names = [visible, stable] + ([parent] if parent else [])
        if extra_parent:
            names.append(extra_parent)
        if kind == EntityKind.PROJECT:
            names.extend(("Customer Code", "Date Received"))
        ids = [_column(columns, name) for name in names]
        company = None
        if kind == EntityKind.PROJECT and any(c.title == "KMV/GALP" for c in columns):
            company = _column(columns, "KMV/GALP")
        wanted = ids + ([company] if company else [])
        top, children = split_hierarchy(
            await client.list_rows(sheet_id, list(dict.fromkeys(wanted)))
        )
        result.append(
            InventorySheet(
                int(sheet_id),
                kind,
                ids[0],
                ids[1],
                top,
                ids[2] if parent else None,
                ids[3] if extra_parent else None,
                (company, ids[2], ids[3]) if kind == EntityKind.PROJECT else None,
                tuple(children),
            )
        )
    for sheet_id, *_ in SHEETS:
        if await client.sheet_workspace_id(sheet_id) != PILOT_WORKSPACE:
            raise ValueError("La hoja ya no pertenece al workspace autorizado")
        if await client.sheet_version(sheet_id) != versions[sheet_id]:
            raise ValueError("Una hoja cambió durante la lectura; volver a intentar")
    return result


def _column(columns: list, name: str) -> str:
    matches = [column.id for column in columns if column.title == name]
    if len(matches) != 1:
        raise ValueError("Columna ausente o duplicada")
    return matches[0]
