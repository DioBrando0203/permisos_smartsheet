# SPEC-B04 Cliente de Smartsheet

Estado: implementada
Código: `services/smartsheet/client.py`, `services/smartsheet/mappers.py`, `services/cache.py`
Relacionadas: ADR-B01, ADR-B03, ADR-B06, SM-01 a SM-08

## Objetivo

Un único punto que habla con la API 2.0 de Smartsheet: autentica, reintenta, pagina, acota la concurrencia y traduce errores a códigos propios, sin filtrar el token ni datos personales.

## Comportamiento

1. Un `httpx.AsyncClient` por proceso con `base_url=SMARTSHEET_BASE_URL`, cabecera `Authorization: Bearer <token>` y plazo `smartsheet_timeout_seconds` (por defecto 20 s). Se crea y cierra en el ciclo de vida de FastAPI.
2. `_request(method, path, *, params, json)` es la única función que envía solicitudes. Toma un cupo del semáforo (`smartsheet_max_concurrency`, por defecto 8).
3. Reintentos: ante 429, 500, 502, 503, 504 o error de red, hasta `smartsheet_max_retries` (por defecto 4) con espera exponencial con variación aleatoria (1, 2, 4, 8 s ± 25 %); si hay `Retry-After`, se respeta. Smartsheet recomienda esta estrategia para el límite de 300 solicitudes por minuto.
4. Las escrituras (POST, PATCH, DELETE) sólo se reintentan ante 429 o 503, donde Smartsheet no aplicó el cambio; ante 500 o error de red no se reintentan para no duplicar (SM-04).
5. Paginación:
   - Endpoints `/shares`: seguir `lastKey` mientras venga.
   - Endpoints clásicos (`/sheets`, `/users`, `/groups`): `includeAll=true`; si la respuesta trae `totalPages > 1`, pedir el resto por `page`.
6. Traducción de errores (cuerpo de Smartsheet `{errorCode, message, refId}`):
   - 401 o `errorCode` 1002/1003: `SMARTSHEET_AUTH` (502 al cliente): token inválido o vencido.
   - 403 o 1004: `SMARTSHEET_FORBIDDEN` (403).
   - 404 o 1006: `NOT_FOUND` (404); el servicio lo especializa (`SHEET_NOT_FOUND`, `SHARE_NOT_FOUND`).
   - 400 con validación: `SMARTSHEET_REJECTED` (422) con el `message` de Smartsheet en `detail.upstream_message` (sin token ni URL).
   - 429 tras agotar reintentos: `SMARTSHEET_RATE_LIMITED` (503).
   - 5xx o red tras agotar reintentos: `SMARTSHEET_UNAVAILABLE` (502).
   - Siempre se incluye `refId` de Smartsheet en `detail.ref_id` para soporte.
7. Logs: método, ruta sin query, estado, intento y duración. Nunca cabeceras, cuerpos, correos ni el token.
8. `mappers.py` convierte JSON en dataclasses `RawSheet`, `RawShare`, `RawUser`, `RawGroup`, tolerando campos ausentes (`name` puede faltar) e ids numéricos o de texto (siempre `str`).

## Caché (ADR-B06)

- `TtlCache` en memoria del proceso, con vencimiento `cache_ttl_seconds` (por defecto 120 s).
- Claves: `sheets`, `shares:{sheet_id}`, `users`, `groups`, `org_users`.
- `invalidate(key)` e `invalidate_prefix(prefix)`.
- Solicitudes simultáneas por la misma clave comparten una sola llamada a Smartsheet (single flight).

## Criterios de aceptación

- CA-01: la cabecera lleva el token y ningún log lo contiene. Prueba: `test_client.py::test_token_is_sent_and_never_logged`.
- CA-02: 429 con `Retry-After` espera y reintenta; al agotar, `SMARTSHEET_RATE_LIMITED`. Prueba: `test_client.py::test_rate_limit_retries_then_fails`.
- CA-03: GET con 500 se reintenta; POST con 500 no. Prueba: `test_client.py::test_writes_are_not_retried_on_500`.
- CA-04: `lastKey` se sigue hasta el final. Prueba: `test_client.py::test_follows_last_key`.
- CA-05: ids numéricos se mapean a texto. Prueba: `test_client.py::test_read_retries_on_500_then_succeeds` (id numérico a texto).
- CA-06: 401 se traduce a `SMARTSHEET_AUTH` con `ref_id`. Prueba: `test_client.py::test_auth_error_is_translated`.
- CA-07: dos lecturas simultáneas de la misma clave hacen una sola llamada. Prueba: `test_permissions.py::test_cache_single_flight_and_invalidation`.
- CA-08: `repr(settings)` no contiene el token. Prueba: `test_security.py::test_token_is_secret`.
- CA-09: sin token no se llama a Smartsheet y responde `TOKEN_MISSING`. Prueba: `test_client.py::test_missing_token_never_calls_smartsheet`.
