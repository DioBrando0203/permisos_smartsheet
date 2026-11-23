"""Lectura de las filas de una hoja, mezcla de `SmartsheetClient` (SPEC-B21 CA-01).

Pide la hoja completa en un solo pedido: comprobado el 2026-11-22 con 2 287 filas en 0,9 s,
contra 13 pedidos de 500 filas por lectura con la maestra 2.0 a fin de año. Si Smartsheet
devolviera menos filas que `totalRowCount`, sigue con páginas como antes. No escribe.
"""

from typing import Any

from app.services.smartsheet import mappers
from app.services.smartsheet.transport import Transport
from app.services.smartsheet.types import RawRow

# Respaldo si faltan filas en la respuesta completa: máximo por página que admite Smartsheet.
_ROWS_PAGE = 500


class RowReads:
    """Mezcla de `SmartsheetClient`: usa su transporte."""

    _transport: Transport

    async def list_rows(
        self,
        sheet_id: str,
        column_ids: list[str],
        *,
        with_authors: bool = False,
        objects: bool = False,
        level: int | None = None,
    ) -> list[RawRow]:
        """Todas las filas, sólo con las columnas pedidas; la primera es la etiqueta.

        Pedir pocas columnas mantiene liviana una hoja de miles de filas y 100+ columnas.
        """
        params = _row_params(column_ids, with_authors=with_authors, objects=objects, level=level)
        label = column_ids[0] if column_ids else None
        data = await self._transport.request("GET", f"/sheets/{sheet_id}", params=params)
        batch = data.get("rows", [])
        if len(batch) >= int(data.get("totalRowCount") or 0):
            return [mappers.to_row(item, label) for item in batch]
        return await self._paged_rows(sheet_id, params, label)

    async def _paged_rows(
        self, sheet_id: str, params: dict[str, Any], label: str | None
    ) -> list[RawRow]:
        rows: list[RawRow] = []
        page = 1
        while True:
            paged = params | {"pageSize": _ROWS_PAGE, "page": page}
            data = await self._transport.request("GET", f"/sheets/{sheet_id}", params=paged)
            batch = data.get("rows", [])
            rows.extend(mappers.to_row(item, label) for item in batch)
            # Smartsheet repite la última página si se pide una mayor: cortar por total.
            if len(batch) < _ROWS_PAGE or len(rows) >= int(data.get("totalRowCount") or 0):
                return rows
            page += 1


def _row_params(
    column_ids: list[str], *, with_authors: bool, objects: bool, level: int | None
) -> dict[str, Any]:
    params: dict[str, Any] = {"columnIds": ",".join(column_ids)}
    if level:
        params["level"] = level
    include = [name for name, on in (("writerInfo", with_authors), ("objectValue", objects)) if on]
    if include:
        params["include"] = ",".join(include)
    return params
