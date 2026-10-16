from fastapi import APIRouter

from app.api.deps import ServicesDep, SheetId
from app.models.automations import AccountAutomations, SheetAutomations

router = APIRouter()


@router.get("/automations")
async def account_automations(
    services: ServicesDep, q: str | None = None, only_problems: bool = False, refresh: bool = False
) -> AccountAutomations:
    """Alertas y flujos de todas las hojas: cuántos funcionan, cuáles están apagados y por qué."""
    return await services.automations.account(q, only_problems, refresh=refresh)


@router.get("/sheets/{sheet_id}/automations")
async def sheet_automations(
    services: ServicesDep, sheet_id: SheetId, refresh: bool = False
) -> SheetAutomations:
    """Cada automatización de la hoja con su diagnóstico: destinatarios, columnas y motivo."""
    return await services.automations.sheet(sheet_id, refresh=refresh)
