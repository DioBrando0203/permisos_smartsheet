"""Calidad de datos de una hoja (SPEC-B09). Sólo lectura.

Lee sólo las columnas que se revisan (más la primaria como etiqueta de cada fila).
"""

import difflib
import re
from dataclasses import dataclass

from app.core.errors import AppError
from app.models.quality import ColumnInfo, QualityCheck, QualityIssue, SheetQuality
from app.services import quality_rules
from app.services.cache import TtlCache
from app.services.sheets import SheetService
from app.services.smartsheet import RawColumn, RawRow, SmartsheetClient

MAX_COLUMNS = 20


@dataclass(frozen=True)
class QualityRequest:
    unique: list[str]
    required: list[str]
    patterns: list[str]  # "Columna=expresión"


@dataclass(frozen=True)
class _Planned:
    column: RawColumn
    check: str
    pattern: re.Pattern[str] | None = None


class QualityService:
    def __init__(self, client: SmartsheetClient, cache: TtlCache, sheets: SheetService) -> None:
        self._client = client
        self._cache = cache
        self._sheets = sheets

    async def columns(self, sheet_id: str) -> list[ColumnInfo]:
        await self._sheets.get(sheet_id)
        return [
            ColumnInfo(id=c.id, title=c.title, type=c.type, index=c.index, primary=c.primary)
            for c in await self._sheets.columns(sheet_id)
        ]

    async def check(
        self, sheet_id: str, request: QualityRequest, *, refresh: bool = False
    ) -> SheetQuality:
        sheet = await self._sheets.get(sheet_id)
        columns = await self._sheets.columns(sheet_id)
        planned = _plan(request, columns)
        label = next((c for c in columns if c.primary), columns[0])
        wanted = [label.id, *dict.fromkeys(p.column.id for p in planned if p.column.id != label.id)]
        rows = await self._rows(sheet_id, wanted, refresh=refresh)
        return SheetQuality(
            sheet=sheet, rows_total=len(rows), checks=[_run(item, rows) for item in planned]
        )

    async def _rows(self, sheet_id: str, column_ids: list[str], *, refresh: bool) -> list[RawRow]:
        async def load() -> list[RawRow]:
            return await self._client.list_rows(sheet_id, column_ids)

        key = f"cells:{sheet_id}:{','.join(column_ids)}"
        return await self._cache.get_or_load(key, load, refresh=refresh)


def _plan(request: QualityRequest, columns: list[RawColumn]) -> list[_Planned]:
    planned = [_Planned(_column(name, columns), "unique") for name in request.unique]
    planned += [_Planned(_column(name, columns), "required") for name in request.required]
    planned += [_pattern_check(item, columns) for item in request.patterns]
    if not planned:
        raise AppError(
            "NO_CHECKS", "Indique al menos una revisión: unique, required o pattern.", 422
        )
    if len({item.column.id for item in planned}) > MAX_COLUMNS:
        raise AppError("TOO_MANY_COLUMNS", f"Revise como máximo {MAX_COLUMNS} columnas.", 422)
    return planned


def _pattern_check(item: str, columns: list[RawColumn]) -> _Planned:
    name, separator, expression = item.partition("=")
    compiled = quality_rules.compile_pattern(expression) if separator else None
    if compiled is None:
        raise AppError(
            "INVALID_PATTERN",
            f"Formato no válido en '{item[:60]}'. Use Columna=expresión, con una expresión "
            f"regular válida de hasta {quality_rules.MAX_PATTERN_LENGTH} caracteres.",
            422,
        )
    return _Planned(_column(name, columns), "pattern", compiled)


def _column(name: str, columns: list[RawColumn]) -> RawColumn:
    """Columna por id o por título sin distinguir mayúsculas; si no, sugiere parecidas."""
    wanted = name.strip()
    for column in columns:
        if column.id == wanted or column.title.casefold() == wanted.casefold():
            return column
    titles = [column.title for column in columns]
    close = difflib.get_close_matches(wanted, titles, n=3, cutoff=0.5)
    hint = f" ¿Quiso decir: {', '.join(close)}?" if close else ""
    raise AppError("COLUMN_NOT_FOUND", f"La columna '{wanted[:60]}' no existe.{hint}", 404)


def _run(item: _Planned, rows: list[RawRow]) -> QualityCheck:
    column_id = item.column.id
    if item.check == "unique":
        issues = quality_rules.duplicates(rows, column_id)
    elif item.check == "required":
        issues = quality_rules.missing(rows, column_id)
    else:
        assert item.pattern is not None
        issues = quality_rules.mismatches(rows, column_id, item.pattern)
    shown, truncated = _limit(issues)
    return QualityCheck(
        column=item.column.title,
        column_id=column_id,
        check=item.check,
        pattern=item.pattern.pattern if item.pattern else None,
        issues_count=quality_rules.issue_count(issues),
        issues=shown,
        truncated=truncated,
    )


def _limit(issues: list[QualityIssue]) -> tuple[list[QualityIssue], bool]:
    """Hasta MAX_ISSUES filas en total en la respuesta; el conteo siempre es completo."""
    shown: list[QualityIssue] = []
    budget = quality_rules.MAX_ISSUES
    for issue in issues:
        if budget <= 0:
            return shown, True
        rows = issue.rows[:budget]
        shown.append(QualityIssue(value=issue.value, rows=rows))
        budget -= len(rows)
    return shown, sum(len(i.rows) for i in issues) > quality_rules.MAX_ISSUES
