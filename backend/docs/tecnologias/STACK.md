# Stack del backend

Rangos en `pyproject.toml`; versiones verificadas en `requirements.lock` cuando se instale por primera vez.

## Ejecución

- Python 3.11+ (verificado en el equipo: 3.14.4). `StrEnum`, `TaskGroup` y `X | None` nativos.
- FastAPI: API tipada con OpenAPI en `/docs`, que sirve para probar el backend antes de tener frontend.
- Uvicorn: un solo proceso en 127.0.0.1 (la caché es por proceso, ADR-B06).
- httpx (`AsyncClient`): cliente HTTP asíncrono con plazos y conexión reutilizada hacia Smartsheet.
- Pydantic v2 y pydantic-settings: contrato HTTP y lectura de `.env` con `SecretStr` para el token.
- Sin SDK oficial de Smartsheet (`smartsheet-python-sdk`): es síncrono y sólo se necesitan unos pocos endpoints; un cliente propio con httpx es más simple de probar con respx y deja el control de reintentos y concurrencia (SPEC-B04). Revisable si el alcance crece.

## Desarrollo

- pytest y pytest-asyncio: pruebas.
- respx: simula `httpx` para que la suite no llame a Smartsheet (QB-02).
- Ruff: lint y formato.

## Restricciones

- Sin ORM, base de datos, colas ni servicios en la nube propios (ADR-B02).
- Dependencia nueva: justificar aquí, fijar en `requirements.lock` y probar en Linux y Windows.

## Fuentes primarias

- [API de Smartsheet 2.0](https://developers.smartsheet.com/api/smartsheet/introduction)
- [Compartir (sharing) en la API](https://developers.smartsheet.com/api/smartsheet/openapi/sharing)
- [Límites de solicitudes y reintentos](https://developers.smartsheet.com/api/smartsheet/guides/advanced-topics/scalability-options)
- [Niveles de acceso](https://help.smartsheet.com/articles/1155182-sharing-permission-levels)
- [FastAPI](https://fastapi.tiangolo.com/), [httpx](https://www.python-httpx.org/), [respx](https://lundberg.github.io/respx/)
