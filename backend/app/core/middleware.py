"""Rechaza escrituras desde orígenes web no autorizados (ADR-B08).

Un sitio cualquiera abierto en el navegador podría enviar un POST al panel local; sin esta
comprobación actuaría con el token de administrador.
"""

from starlette.types import ASGIApp, Receive, Scope, Send

from app.core.errors import AppError, error_response

_SAFE_METHODS = frozenset({"GET", "HEAD", "OPTIONS"})


class OriginMiddleware:
    def __init__(self, app: ASGIApp, allowed_origins: tuple[str, ...]) -> None:
        self.app = app
        self.allowed_origins = frozenset(allowed_origins)

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http" or scope["method"] in _SAFE_METHODS:
            await self.app(scope, receive, send)
            return
        headers = dict(scope["headers"])
        origin = headers.get(b"origin", b"").decode("latin-1")
        if origin and origin not in self.allowed_origins:
            error = AppError(
                "ORIGIN_NOT_ALLOWED", "Origen no autorizado para modificar permisos.", 403
            )
            await error_response(error)(scope, receive, send)
            return
        await self.app(scope, receive, send)
