"""Inventario del piloto: sólo lecturas y comprobación de workspace en vivo."""

from app.services.ids.dry_run import PILOT_WORKSPACE
from app.services.ids.formats import EntityKind
from app.services.ids.inventory import InventorySheet
from app.services.smartsheet import SmartsheetClient

# Lista explícita, verificada por lectura con el usuario; no autoriza escrituras.
SHEETS = (
    ("4365321059389316", EntityKind.PROJECT, "Tracking Project", "Stable Tracking Project", None),
    ("73093952524164", EntityKind.TASK, "Task ID", "Stable Task ID", "Tracking Project"),
    ("8140679218941828", EntityKind.RECORD, "Request ID", "Stable Request ID", "Task ID"),
    ("5463681132613508", EntityKind.REVISION, "Revision ID", "Stable Revision ID", "Task ID"),
)


async def read_pilot(client: SmartsheetClient) -> list[InventorySheet]:
    """Exige pertenencia actual y columnas exactas; no reutiliza caché."""
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
        ids = []
        for name in names:
            matches = [column.id for column in columns if column.title == name]
            if len(matches) != 1:
                raise ValueError("Columna ausente o duplicada")
            ids.append(matches[0])
        rows = await client.list_rows(sheet_id, list(dict.fromkeys(ids)))
        result.append(
            InventorySheet(
                int(sheet_id),
                kind,
                ids[0],
                ids[1],
                rows,
                ids[2] if parent else None,
                ids[3] if extra_parent else None,
            )
        )
    for sheet_id, *_ in SHEETS:
        if await client.sheet_workspace_id(sheet_id) != PILOT_WORKSPACE:
            raise ValueError("La hoja ya no pertenece al workspace autorizado")
        if await client.sheet_version(sheet_id) != versions[sheet_id]:
            raise ValueError("Una hoja cambió durante la lectura; volver a intentar")
    return result
