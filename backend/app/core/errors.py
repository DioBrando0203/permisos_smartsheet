"""Error con código estable y mensaje seguro para el usuario, y su manejador HTTP."""

from fastapi import Request
from fastapi.responses import JSONResponse


class AppError(Exception):
    """Error esperable: código en MAYÚSCULAS para el frontend y mensaje en español (PY-15)."""

    def __init__(
        self,
        code: str,
        message: str,
        status: int,
        *,
        ref_id: str | None = None,
        upstream_message: str | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status = status
        self.ref_id = ref_id
        self.upstream_message = upstream_message

    def to_detail(self) -> dict[str, str | None]:
        return {
            "code": self.code,
            "message": self.message,
            "ref_id": self.ref_id,
            "upstream_message": self.upstream_message,
        }


def error_response(error: AppError) -> JSONResponse:
    return JSONResponse({"detail": error.to_detail()}, status_code=error.status)


async def app_error_handler(_request: Request, error: Exception) -> JSONResponse:
    assert isinstance(error, AppError)
    return error_response(error)
