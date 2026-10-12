"""Traducción de respuestas de error de Smartsheet a `AppError` con código estable (SPEC-B04)."""

import httpx

from app.core.errors import AppError

_AUTH_CODES = {1002, 1003}
_FORBIDDEN_CODES = {1004}
_NOT_FOUND_CODES = {1006}


def translate_error(response: httpx.Response) -> AppError:
    """Convierte un 4xx/5xx en un error seguro: sin token, URL ni cuerpo crudo."""
    body = _json(response)
    code = body.get("errorCode")
    ref_id = body.get("refId")
    upstream = body.get("message") if isinstance(body.get("message"), str) else None
    status = response.status_code
    if status == 401 or code in _AUTH_CODES:
        return AppError(
            "SMARTSHEET_AUTH",
            "Smartsheet rechazó el token. Revise SMARTSHEET_ACCESS_TOKEN en backend/.env.",
            502,
            ref_id=ref_id,
        )
    if status == 403 or code in _FORBIDDEN_CODES:
        return AppError(
            "SMARTSHEET_FORBIDDEN",
            "Smartsheet no permite esta operación con la cuenta del token.",
            403,
            ref_id=ref_id,
            upstream_message=upstream,
        )
    if status == 404 or code in _NOT_FOUND_CODES:
        return AppError("NOT_FOUND", "Smartsheet no encontró el recurso.", 404, ref_id=ref_id)
    if status == 429:
        return rate_limited(ref_id)
    if status >= 500:
        return unavailable(ref_id)
    return AppError(
        "SMARTSHEET_REJECTED",
        "Smartsheet rechazó los datos enviados.",
        422,
        ref_id=ref_id,
        upstream_message=upstream,
    )


def rate_limited(ref_id: str | None = None) -> AppError:
    return AppError(
        "SMARTSHEET_RATE_LIMITED",
        "Smartsheet está limitando las solicitudes. Espere un minuto e inténtelo de nuevo.",
        503,
        ref_id=ref_id,
    )


def unavailable(ref_id: str | None = None) -> AppError:
    return AppError(
        "SMARTSHEET_UNAVAILABLE",
        "Smartsheet no respondió. Inténtelo de nuevo en unos minutos.",
        502,
        ref_id=ref_id,
    )


def token_missing() -> AppError:
    return AppError(
        "TOKEN_MISSING",
        "Falta SMARTSHEET_ACCESS_TOKEN en backend/.env.",
        503,
    )


def _json(response: httpx.Response) -> dict:
    try:
        data = response.json()
    except ValueError:
        return {}
    return data if isinstance(data, dict) else {}
