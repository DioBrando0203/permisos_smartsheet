"""Carga de trabajo y acceso de los diseñadores en todas las hojas (SPEC-B12). Sólo lectura.

Combina filas (columnas de diseñador y estado), el directorio de personas, los permisos de
cada hoja y, si se configura, el catálogo de diseñadores.
"""

import asyncio
from dataclasses import dataclass

from app.core.config import Settings, split_list
from app.core.errors import AppError
from app.models.designers import (
    DesignerLoad,
    DesignerPerson,
    DesignerSheet,
    DesignerWorkload,
    SheetGap,
)
from app.models.people import FailedSheet, Person
from app.services import workload_rules as rules
from app.services.bulk_plans import effective_levels
from app.services.people import PeopleService
from app.services.quality import QualityService, find_column
from app.services.references import ReferenceService
from app.services.search import matches, normalize
from app.services.shares import ShareService
from app.services.sheets import SheetService
from app.services.smartsheet import RawColumn, RawRow, RawSheet


@dataclass(frozen=True)
class WorkloadRequest:
    query: str | None
    designer_columns: list[str]
    status_column: str
    closed_statuses: list[str]


@dataclass(frozen=True)
class _SheetResult:
    sheet: RawSheet
    accumulators: dict[str, rules.DesignerAccumulator]
    gap: SheetGap
    header_rows: int


class DesignerService:
    def __init__(
        self,
        settings: Settings,
        sheets: SheetService,
        shares: ShareService,
        people: PeopleService,
        quality: QualityService,
        references: ReferenceService,
    ) -> None:
        self._settings = settings
        self._sheets = sheets
        self._shares = shares
        self._people = people
        self._quality = quality
        self._references = references

    def default_request(self, query: str | None) -> WorkloadRequest:
        return WorkloadRequest(
            query=query,
            designer_columns=list(split_list(self._settings.app_designer_columns)),
            status_column=self._settings.app_status_column,
            closed_statuses=list(split_list(self._settings.app_closed_statuses)),
        )

    async def workload(
        self, request: WorkloadRequest, *, refresh: bool = False
    ) -> DesignerWorkload:
        sheets = [
            s
            for s in await self._sheets.raw_sheets(refresh=refresh)
            if s.in_my_list and matches(request.query, s.name)
        ]
        results = await asyncio.gather(*(self._safe(s, request, refresh) for s in sheets))
        done = [item for item in results if isinstance(item, _SheetResult)]
        merged = _merge([item.accumulators for item in done])
        people = (await self._people.list(None, None)).people
        catalog = await self._catalog()
        loads = [await self._load(acc, people, catalog, refresh) for acc in merged.values()]
        return DesignerWorkload(
            designer_columns=request.designer_columns,
            status_column=request.status_column,
            closed_statuses=request.closed_statuses,
            sheets_reviewed=len(sheets) - sum(1 for r in results if isinstance(r, FailedSheet)),
            sheets_with_designers=len(done),
            open_total=sum(load.open for load in loads),
            on_hold_total=sum(load.on_hold for load in loads),
            closed_total=sum(load.closed for load in loads),
            header_like_rows=sum(item.header_rows for item in done),
            designers=sorted(loads, key=lambda d: (-d.open, -d.on_hold, normalize(d.name))),
            sheet_gaps=sorted(
                (item.gap for item in done if item.gap.open_without_designer),
                key=lambda gap: -gap.open_without_designer,
            ),
            failed_sheets=[item for item in results if isinstance(item, FailedSheet)],
        )

    async def _safe(
        self, sheet: RawSheet, request: WorkloadRequest, refresh: bool
    ) -> _SheetResult | FailedSheet | None:
        """Una hoja sin columnas de diseñador devuelve `None`; un fallo se informa (Bulkhead)."""
        try:
            return await self._sheet(sheet, request, refresh)
        except AppError as error:
            return FailedSheet(sheet_id=sheet.id, sheet_name=sheet.name, code=error.code)

    async def _sheet(
        self, sheet: RawSheet, request: WorkloadRequest, refresh: bool
    ) -> _SheetResult | None:
        columns = await self._sheets.columns(sheet.id)
        designer_columns = _existing(request.designer_columns, columns)
        if not designer_columns:
            return None
        status = _existing([request.status_column], columns)
        label = next((c for c in columns if c.primary), columns[0])
        wanted = list(dict.fromkeys([label.id, *(c.id for c in designer_columns + status)]))
        rows = await self._quality.rows(sheet.id, wanted, refresh=refresh)
        return _summarize(sheet, rows, designer_columns, status[0] if status else None, request)

    async def _load(
        self,
        acc: rules.DesignerAccumulator,
        people: list[Person],
        catalog: set[str] | None,
        refresh: bool,
    ) -> DesignerLoad:
        person, ambiguous = rules.match_person(acc.name, people)
        sheets = [await self._sheet_access(load, person, refresh) for load in acc.sheets.values()]
        return DesignerLoad(
            name=acc.name,
            in_catalog=None if catalog is None else acc.name.strip().casefold() in catalog,
            person=DesignerPerson(key=person.key, email=person.email, name=person.name)
            if person
            else None,
            ambiguous=ambiguous,
            open=acc.total("open"),
            on_hold=acc.total("on_hold"),
            closed=acc.total("closed"),
            by_phase=dict(sorted(acc.phases.items())),
            sheets_without_access=sum(
                1 for s in sheets if s.has_access is False and (s.open or s.on_hold)
            ),
            sheets=sorted(sheets, key=lambda s: (-s.open, s.sheet_name.casefold())),
        )

    async def _sheet_access(
        self, load: rules.SheetLoad, person: Person | None, refresh: bool
    ) -> DesignerSheet:
        level = None
        has_access = None
        if person is not None and person.email:
            levels = effective_levels(await self._shares.raw_shares(load.sheet_id, refresh=refresh))
            entry = levels.get(person.email)
            has_access = entry is not None
            level = entry.level if entry else None
        return DesignerSheet(
            sheet_id=load.sheet_id,
            sheet_name=load.sheet_name,
            open=load.states["open"],
            on_hold=load.states["on_hold"],
            closed=load.states["closed"],
            has_access=has_access,
            access_level=level,
        )

    async def _catalog(self) -> set[str] | None:
        sheet = self._settings.app_designer_catalog_sheet.strip()
        if not sheet:
            return None
        column = self._settings.app_designer_catalog_column
        try:
            return (await self._references.catalog(sheet, column)).values
        except AppError:
            return None


def _existing(names: list[str], columns: list[RawColumn]) -> list[RawColumn]:
    found: list[RawColumn] = []
    for name in names:
        try:
            found.append(find_column(name, columns))
        except AppError:
            continue
    return found


def _summarize(
    sheet: RawSheet,
    rows: list[RawRow],
    designer_columns: list[RawColumn],
    status: RawColumn | None,
    request: WorkloadRequest,
) -> _SheetResult:
    closed = {value.strip().casefold() for value in request.closed_statuses}
    headers = {column.title.casefold() for column in designer_columns}
    ids = [column.id for column in designer_columns]
    accumulators: dict[str, rules.DesignerAccumulator] = {}
    unassigned = without_status = header_rows = 0
    for row in rows:
        if rules.has_header_value(row, ids, headers):
            # Fila de encabezados copiada como dato: no es trabajo; se cuenta aparte.
            header_rows += 1
            continue
        value = row.cells.get(status.id) if status else None
        state = rules.row_state(value, closed)
        without_status += rules.is_placeholder(value)
        names = rules.designers_in_row(row, ids, headers)
        if not names and state != "closed":
            unassigned += 1
        for name in names:
            acc = accumulators.setdefault(normalize(name), rules.DesignerAccumulator(name))
            acc.add(sheet.id, sheet.name, state, rules.phase_of(value))
    gap = SheetGap(
        sheet_id=sheet.id,
        sheet_name=sheet.name,
        open_without_designer=unassigned,
        without_status=without_status,
    )
    return _SheetResult(sheet, accumulators, gap, header_rows)


def _merge(
    per_sheet: list[dict[str, rules.DesignerAccumulator]],
) -> dict[str, rules.DesignerAccumulator]:
    merged: dict[str, rules.DesignerAccumulator] = {}
    for accumulators in per_sheet:
        for key, acc in accumulators.items():
            target = merged.setdefault(key, rules.DesignerAccumulator(acc.name))
            target.phases.update(acc.phases)
            target.sheets.update(acc.sheets)
    return merged
