"""Dependencias del procesador y del catálogo de Smartsheet."""

from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, Request

from app.core.config import Settings
from app.services.cache import TtlCache
from app.services.quality import QualityService
from app.services.sheets import SheetService
from app.services.smartsheet import SmartsheetClient


@dataclass(frozen=True)
class Services:
    settings: Settings
    client: SmartsheetClient
    cache: TtlCache
    sheets: SheetService
    quality: QualityService


def build_services(settings: Settings, client: SmartsheetClient | None = None) -> Services:
    client = client or SmartsheetClient(settings)
    cache = TtlCache(settings.cache_ttl_seconds)
    sheets = SheetService(client, cache, settings.dynamic_view_sheets)
    return Services(settings, client, cache, sheets, QualityService(client, cache, sheets))


def get_services(request: Request) -> Services:
    return request.app.state.services


ServicesDep = Annotated[Services, Depends(get_services)]
