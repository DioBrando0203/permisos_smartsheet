"""Dependencias de FastAPI: servicios creados una vez por app y guardados en `app.state`."""

from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, Path, Request

from app.core.config import Settings
from app.services.account_review import AccountReviewService
from app.services.activity import ActivityService
from app.services.automations import AutomationService
from app.services.bulk import BulkService
from app.services.cache import TtlCache
from app.services.designers import DesignerService
from app.services.export import ExportService
from app.services.gis import GisClient
from app.services.map import MapService
from app.services.people import PeopleService
from app.services.quality import QualityService
from app.services.references import ReferenceService
from app.services.reports import ReportService
from app.services.shares import ShareService
from app.services.sheets import SheetService
from app.services.smartsheet import SmartsheetClient

# Hoja real usada como ejemplo en Swagger: "8. Crown Castle Fiber - Engineering Plan 2026".
EXAMPLE_SHEET_ID = "1842596423880580"
EXAMPLE_SHEET_PERMALINK = "QMFVM7v3V23HqwgmCwHg5wF8XHFr5GCG4WJjXJF1"
# Plan del año anterior, para comparar y copiar: "7. Crown Castle Fiber - Engineering Plan 2025".
EXAMPLE_PREVIOUS_SHEET_ID = "5750050894335876"

# Sólo letras y dígitos: impide inyectar rutas en la URL de la API de Smartsheet.
SheetRef = Annotated[
    str,
    Path(
        alias="sheet_id",
        pattern=r"^[A-Za-z0-9]{1,64}$",
        description=(
            "Id numérico de la hoja o código del permalink que se ve en el navegador "
            "(https://app.smartsheet.com/sheets/<código>)."
        ),
        openapi_examples={
            "id": {"summary": "Id numérico", "value": EXAMPLE_SHEET_ID},
            "permalink": {"summary": "Código del permalink", "value": EXAMPLE_SHEET_PERMALINK},
        },
    ),
]
ShareId = Annotated[str, Path(pattern=r"^[A-Za-z0-9_-]{1,64}$", description="Id del permiso")]


@dataclass(frozen=True)
class Services:
    settings: Settings
    client: SmartsheetClient
    cache: TtlCache
    sheets: SheetService
    shares: ShareService
    people: PeopleService
    reports: ReportService
    bulk: BulkService
    review: AccountReviewService
    activity: ActivityService
    quality: QualityService
    export: ExportService
    automations: AutomationService
    references: ReferenceService
    designers: DesignerService
    maps: MapService


def build_services(settings: Settings, client: SmartsheetClient | None = None) -> Services:
    client = client or SmartsheetClient(settings)
    cache = TtlCache(settings.cache_ttl_seconds)
    sheets = SheetService(client, cache, settings.dynamic_view_sheets)
    shares = ShareService(client, cache, sheets, read_only=settings.app_read_only)
    people = PeopleService(client, cache, sheets, shares)
    reports = ReportService(sheets, shares, people)
    bulk = BulkService(sheets, shares, people)
    review = AccountReviewService(sheets, people, reports)
    activity = ActivityService(client, cache, sheets, shares)
    quality = QualityService(client, cache, sheets)
    export = ExportService(sheets, people)
    automations = AutomationService(client, cache, sheets, shares)
    references = ReferenceService(sheets, quality)
    designers = DesignerService(settings, sheets, shares, people, quality, references)
    maps = MapService(settings, GisClient(settings), TtlCache(settings.gis_cache_ttl_seconds))
    return Services(
        settings,
        client,
        cache,
        sheets,
        shares,
        people,
        reports,
        bulk,
        review,
        activity,
        quality,
        export,
        automations,
        references,
        designers,
        maps,
    )


def get_services(request: Request) -> Services:
    return request.app.state.services


ServicesDep = Annotated[Services, Depends(get_services)]


async def resolve_sheet_id(services: ServicesDep, sheet_ref: SheetRef) -> str:
    return await services.sheets.resolve_id(sheet_ref)


SheetId = Annotated[str, Depends(resolve_sheet_id)]
