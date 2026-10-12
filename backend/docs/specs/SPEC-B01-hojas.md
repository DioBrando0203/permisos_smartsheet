# SPEC-B01 Hojas

Estado: implementada
Código: `api/routes/sheets.py`, `services/sheets.py`, `services/smartsheet/client.py`
Relacionadas: SPEC-B04, ADR-B06, ADR-B07

## Objetivo

Listar las hojas a las que el token tiene acceso para elegir cuál revisar, y dar el detalle básico de una.

## Fuente en Smartsheet

- `GET /2.0/sheets?includeAll=true`: devuelve `data[]` con `id`, `name`, `accessLevel`, `permalink`, `createdAt`, `modifiedAt`. Verificado el 2026-10-12: 100 hojas, `totalCount` 100.
- `GET /2.0/sheets/{sheetId}?pageSize=1`: sólo antes de escribir, para leer el nivel actual del token (SM-06).

## Comportamiento

1. `GET /api/sheets` devuelve `SheetList` (`sheets`, `total`, `loaded_at`) con `SheetSummary[]` ordenado por nombre (sin distinguir mayúsculas ni tildes).
2. Parámetro opcional `q`: filtra por nombre, sin distinguir mayúsculas ni tildes; vacío equivale a sin filtro.
3. Parámetro opcional `refresh=true`: ignora la caché y vuelve a leer de Smartsheet.
4. Cada hoja indica `can_manage_shares`: `true` si el nivel del token es `ADMIN` u `OWNER` (SM-06).
5. `GET /api/sheets/{sheet_id}` devuelve `SheetSummary` (los permisos, propietario incluido, salen de SPEC-B02).
6. Una hoja inexistente o sin acceso responde 404 `SHEET_NOT_FOUND`.
7. Toda ruta con `{sheet_id}` acepta el id numérico (`1842596423880580`) o el código del permalink que se ve en el navegador (`QMFVM7v3V23HqwgmCwHg5wF8XHFr5GCG4WJjXJF1` de `https://app.smartsheet.com/sheets/<código>?view=grid`). El código se resuelve al id buscando el permalink en el listado en caché; las respuestas siempre devuelven el id numérico.
8. Swagger muestra como ejemplo una hoja real de la cuenta (`1842596423880580`).

## Criterios de aceptación

- CA-01: el listado mapea `id` a texto, nombre, nivel, enlace y fecha. Prueba: `test_people.py::test_sheets_search_ignores_case_and_accents`.
- CA-02: `q` filtra sin tildes ni mayúsculas. Prueba: `test_people.py::test_sheets_search_ignores_case_and_accents`.
- CA-03: la segunda lectura no llama a Smartsheet y `refresh=true` sí. Prueba: `test_shares.py::test_writes_invalidate_cache` (misma caché) y verificación manual.
- CA-04: `can_manage_shares` es `true` sólo para `ADMIN` y `OWNER`. Prueba: `test_permissions.py::test_manage_shares_requires_admin`.
- CA-05: 404 de Smartsheet se traduce a `SHEET_NOT_FOUND`. Prueba: `test_people.py::test_failed_sheet_marks_incomplete` (traducción a `SHEET_NOT_FOUND`).
- CA-07: el código del permalink se resuelve al id; uno desconocido responde `SHEET_NOT_FOUND` sin llamar a los permisos. Prueba: `test_people.py::test_sheet_can_be_found_by_permalink_code`.
- CA-06: lectura real devuelve las 100 hojas. Prueba: manual, verificada el 2026-10-12 (RESULTADOS).

## Pendientes

- Carpetas y workspaces de cada hoja (PEN-10).
