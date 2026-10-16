from typing import Literal

from fastapi import APIRouter

from app.api.deps import ServicesDep
from app.models.reports import AccountReview

router = APIRouter()


@router.get("/review")
async def account_review(
    services: ServicesDep,
    q: str | None = None,
    min_severity: Literal["high", "medium", "info"] = "medium",
    refresh: bool = False,
) -> AccountReview:
    """Riesgos de toda la cuenta: hojas con alertas y personas que más se repiten.

    Mismas reglas que la auditoría por hoja. La primera vez lee todas las hojas.
    """
    return await services.review.review(q, min_severity, refresh=refresh)
