"""Adaptador de Smartsheet para IDs; la comprobación previa no es atómica."""

import asyncio

from app.core.errors import AppError
from app.services.ids import pilot
from app.services.ids.connector import ChildSnapshot, Snapshot, Target, WriteUncertain
from app.services.ids.dry_run import PILOT_WORKSPACE
from app.services.ids.formats import EntityKind, project_scope
from app.services.ids.store import IdStore
from app.services.smartsheet import RawRow, SmartsheetClient

_MAX_DEPTH = 20  # jerarquía acotada: evita ciclos ante datos inesperados


class SmartsheetIdGateway:
    def __init__(self, client: SmartsheetClient, store: IdStore) -> None:
        self._client = client
        self._store = store

    async def read(self, target: Target) -> Snapshot:
        spec = pilot.sheet_spec(target.sheet_id)
        if spec is None or spec[1] != target.kind:
            return Snapshot(None, "", False, "", "")
        sheet_id = str(target.sheet_id)
        workspace = await self._client.sheet_workspace_id(sheet_id)
        if workspace != PILOT_WORKSPACE:
            return Snapshot(workspace, "", False, "", "")
        columns = await self._client.list_columns(sheet_id)
        by_title = {column.title: column.id for column in columns}
        if len(by_title) != len(columns) or spec[2] not in by_title or spec[3] not in by_title:
            raise ValueError("Columnas del piloto inválidas")
        row = await self._client.get_row(sheet_id, str(target.row_id))
        visible = (row.cells.get(by_title[spec[2]]) or "").strip()
        stable = (row.cells.get(by_title[spec[3]]) or "").strip()
        if row.parent_id:
            # Una fila hija no recibe número propio: hereda el de su madre (`read_child`).
            return Snapshot(workspace, "", False, visible, stable)
        parent = target.parent
        if spec[4]:
            if spec[4] not in by_title:
                raise ValueError("Columna de referencia ausente")
            parent = (row.cells.get(by_title[spec[4]]) or "").strip()
            if target.kind == EntityKind.TASK:
                # Vacía (fila creada sin formulario) se acepta; distinta es ambigua.
                reference = (row.cells.get(by_title.get("Reference", "")) or "").strip()
                if reference and reference != parent:
                    return Snapshot(workspace, "", False, visible, stable)
        else:
            # El ámbito sale de los datos de la fila; la fórmula sólo propone el número.
            parent = _project_scope(row, by_title)
        confirmed = target.kind == EntityKind.PROJECT or await self._parent_confirmed(
            target, parent
        )
        return Snapshot(workspace, parent, confirmed, visible, stable)

    async def _parent_confirmed(self, target: Target, value: str) -> bool:
        spec = pilot.parent_spec(target.kind)
        if spec is None:
            return False
        parent_sheet, title = int(spec[0]), spec[3]
        row_id = await asyncio.to_thread(self._store.confirmed_parent, parent_sheet, value)
        if (
            row_id is None
            or await self._client.sheet_workspace_id(str(parent_sheet)) != PILOT_WORKSPACE
        ):
            return False
        columns = await self._client.list_columns(str(parent_sheet))
        ids = [column.id for column in columns if column.title == title]
        if len(ids) != 1:
            return False
        row = await self._client.get_row(str(parent_sheet), str(row_id))
        return (row.cells.get(ids[0]) or "").strip() == value

    async def write_if_unchanged(self, target: Target, previous: Snapshot, value: str) -> bool:
        """Relee antes de escribir; una edición externa simultánea todavía puede competir."""
        if previous.stable or await self.read(target) != previous:
            return False
        return await self._put(target, value)

    async def read_child(self, target: Target) -> ChildSnapshot:
        """Fila hija y su fila de primer nivel; root_row None si no es hija."""
        spec = pilot.sheet_spec(target.sheet_id)
        sheet_id = str(target.sheet_id)
        workspace = await self._client.sheet_workspace_id(sheet_id)
        if spec is None or workspace != PILOT_WORKSPACE:
            return ChildSnapshot(workspace, None, "", "")
        ids = [c.id for c in await self._client.list_columns(sheet_id) if c.title == spec[3]]
        if len(ids) != 1:
            raise ValueError("Columna Stable ID ausente o duplicada")
        row = await self._client.get_row(sheet_id, str(target.row_id))
        stable = (row.cells.get(ids[0]) or "").strip()
        root = row
        for _ in range(_MAX_DEPTH):
            if not root.parent_id:
                break
            root = await self._client.get_row(sheet_id, root.parent_id)
        if root is row or root.parent_id:
            return ChildSnapshot(workspace, None, "", stable)
        return ChildSnapshot(
            workspace, int(root.id), (root.cells.get(ids[0]) or "").strip(), stable
        )

    async def write_child(self, target: Target, value: str) -> bool:
        return await self._put(target, value)

    async def replace_copy(self, target: Target, copied: str, value: str) -> bool:
        """Copia de una madre: cambia su ID sólo si todavía es el copiado."""
        return await self._put(target, value, copied)

    async def read_stable(self, target: Target, row_id: int) -> str:
        """Stable ID actual de otra fila de la misma hoja; vacío si ya no existe."""
        spec = pilot.sheet_spec(target.sheet_id)
        sheet_id = str(target.sheet_id)
        ids = [c.id for c in await self._client.list_columns(sheet_id) if c.title == spec[3]]
        try:
            row = await self._client.get_row(sheet_id, str(row_id))
        except AppError as error:
            if error.code == "NOT_FOUND":
                return ""
            raise
        return (row.cells.get(ids[0]) or "").strip() if len(ids) == 1 else ""

    async def _put(self, target: Target, value: str, expected: str = "") -> bool:
        """Escribe sólo si la celda contiene `expected`; respuesta incierta -> WriteUncertain."""
        try:
            await self._client.update_stable_id_once(
                str(target.sheet_id), str(target.row_id), value, expected
            )
        except AppError as error:
            if error.code in ("IDS_STABLE_EXISTS", "IDS_STABLE_CHANGED"):
                return False
            if error.status >= 500:
                raise WriteUncertain() from None
            raise
        return True


def _project_scope(row: RawRow, columns: dict[str, str]) -> str:
    """Obtiene el año del valor ISO de Date Received, no de su texto localizado."""
    company = (row.cells.get(columns.get("KMV/GALP", "")) or "").strip()
    if "KMV/GALP" not in columns:
        company = pilot.DEFAULT_COMPANY
    customer = (row.cells.get(columns.get("Customer Code", "")) or "").strip()
    received = row.date_cells.get(columns.get("Date Received", ""))
    return project_scope(company, customer, received)
