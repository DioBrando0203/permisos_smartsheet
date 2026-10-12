# Reglas de programación (Python)

Obligatorias. Citar el ID en revisiones y bitácora. Patrones concretos en `patrones/PATRONES.md`.

## Tamaño y responsabilidad

- PY-01: un módulo de `app/`, una responsabilidad. Máximo 300 líneas. En `tests/`, un archivo por módulo o paquete probado. Al acercarse a 250, dividir por responsabilidad en un paquete con `__init__.py` como fachada.
- PY-02: una función hace una cosa. Objetivo 30 líneas; máximo 60. Si necesita comentarios de "paso 1, paso 2", extraer funciones con nombre.
- PY-03: máximo 5 parámetros. Con más, agrupar en un `@dataclass` (Parameter Object).
- PY-04: máximo 3 niveles de indentación dentro de una función. Usar retornos tempranos (guard clauses).
- PY-05: el nombre del módulo dice qué contiene (`shares.py`, `rules.py`, no `utils.py` ni `helpers.py`).

## Reutilización

- PY-06: antes de escribir una función, buscar si existe (`rg "def nombre"`); ampliar la existente si encaja.
- PY-07: regla de tres: la segunda copia se tolera, la tercera obliga a extraer.
- PY-08: constantes con nombre en lugar de literales repetidos (`AccessLevel.OWNER`, `SHARES_PATH`, no `"OWNER"` o `"/shares"` repartidos).
- PY-09: la API pública de un paquete se expone en su `__init__.py` con `__all__`; otros paquetes importan desde ahí.
- PY-10: lo privado del módulo lleva prefijo `_`. Si otro módulo lo necesita, se vuelve público y se documenta.

## Tipado y datos

- PY-11: anotar tipos en toda función. `X | None` en lugar de `Optional`. Sin `Any` salvo el JSON crudo de Smartsheet dentro de `mappers.py` (frontera con datos no tipados).
- PY-12: datos internos con `@dataclass(frozen=True)`; contrato HTTP con Pydantic. Prohibido devolver tuplas de más de 2 elementos.
- PY-13: niveles de acceso y tipos con `StrEnum` (`AccessLevel`, `ShareType`, `ShareScope`, `LockedReason`), nunca texto libre.
- PY-14: el contrato HTTP sólo cambia en `models/` y se refleja en `estilos/API.md` y, cuando exista, en `frontend/src/lib/types.ts`.

## Errores

- PY-15: errores esperables se lanzan como `AppError(code, message, status)`. Mensaje en español, sin token, URL de Smartsheet ni trazas.
- PY-16: `except Exception` sólo en fronteras de tolerancia (una hoja dentro de la vista por usuario) y siempre registrando el fallo en la respuesta (`failed_sheets`). Nunca `except: pass`.
- PY-17: re-lanzar con `from error` para conservar la causa; `from None` cuando la causa expondría datos sensibles.

## Asincronía y recursos

- PY-18: todo el acceso a Smartsheet es `async` con `httpx.AsyncClient`. Prohibido `requests` o llamadas bloqueantes dentro de rutas.
- PY-19: concurrencia con `asyncio.TaskGroup` o `gather` acotado por el semáforo del cliente; nunca tareas sin límite.
- PY-20: el cliente httpx se crea y cierra en el `lifespan`; no crear un cliente por solicitud.

## Funciones puras y efectos

- PY-21: reglas de permisos, orden, filtros y agregaciones son funciones puras que reciben dataclasses y devuelven valores; se prueban sin red.
- PY-22: sin estado global mutable salvo la caché, que vive en `app.state` y se inyecta. `settings` es inmutable; las pruebas lo reemplazan con `dataclasses.replace` o dependencias de FastAPI.

## Smartsheet

- SM-01: el token sólo se lee en `core/config.py` como `SecretStr` y sólo se usa en `client.py`. No aparece en `repr`, logs, errores, respuestas, pruebas ni docs.
- SM-02: toda llamada a Smartsheet pasa por `SmartsheetClient._request`. Prohibido `httpx` directo en otro módulo.
- SM-03: el JSON de Smartsheet nunca sale del paquete `smartsheet`: se mapea a dataclasses `Raw*` en `mappers.py`.
- SM-04: reintentar lecturas ante 429, 5xx y red; escrituras sólo ante 429 y 503 (no duplicar cambios).
- SM-05: respetar `smartsheet_max_concurrency` y `Retry-After`; no bajarlos para acelerar.
- SM-06: antes de escribir, comprobar con datos frescos que el token es `ADMIN` u `OWNER` de la hoja y aplicar `permissions.rules`. La regla decide; la ruta no repite condiciones.
- SM-07: `sendEmail=false` salvo que la solicitud lo pida explícitamente.
- SM-08: tras una escritura, invalidar la caché afectada y responder con el estado releído de Smartsheet.

## Documentación en código

- PY-23: docstring de módulo que diga su responsabilidad y lo que no hace.
- PY-24: docstring en funciones públicas y en las privadas cuya intención no sea obvia; explicar el porqué.
- PY-25: los límites y protecciones llevan comentario del riesgo que evitan.
