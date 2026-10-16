# Arquitectura del backend

Servicio que lista hojas de Smartsheet, muestra quién tiene acceso a cada una y crea, cambia o quita permisos. Decisiones y motivos en `decisiones/ADR.md`.

Estado: implementado (2026-10-12). Servidor de desarrollo en `127.0.0.1:8710`.

## Capas

```text
api/routes          HTTP: valida, llama al servicio, responde
services/<dominio>  sheets, shares, users: casos de uso y uso de la caché
services/permissions reglas puras: niveles, qué es editable, validación de altas
services/smartsheet cliente HTTP de la API 2.0 y mapeo de su JSON
services/cache      caché en memoria con vencimiento e invalidación por hoja
models, core        contrato Pydantic, configuración, errores, middleware
```

Dependencias permitidas, siempre hacia abajo:

- `api` importa servicios de dominio, `models` y `core`. Nunca `smartsheet` directamente.
- Servicios de dominio importan `smartsheet`, `permissions`, `cache`, `models` y `core`.
- `smartsheet` importa sólo `core` y sus propios dataclasses. No conoce FastAPI ni `models`.
- `permissions` es puro: sólo la biblioteca estándar y sus tipos. Sin E/S.
- `models` y `core` no importan servicios con E/S; `models` sí usa los enums puros de `permissions` y `bulk_plans.StepAction`.
- Prohibido el import circular; si aparece, extraer lo común a un módulo inferior.

## Paquetes y módulos

```text
app/
  launcher.py                    arranque: puerto 8710 o uno libre, APP_PORT y Uvicorn (iniciar.py lo llama)
  main.py                        create_app: CORS, Origin, Host, errores y cierre del cliente httpx
  api/deps.py                    build_services (cliente, caché, servicios) en app.state; SheetId, ShareId
  api/router.py                  agrupa rutas bajo /api
  api/routes/health.py           GET /health (con read_only), GET /me
  api/routes/sheets.py           GET /sheets, GET /sheets/{id}; GET, POST /sheets/{id}/shares; PATCH, DELETE /sheets/{id}/shares/{share_id}
  api/routes/people.py           GET /users, GET /users/{key}, GET /contacts, GET /groups, GET /review
  api/routes/reports.py          GET /sheets/compare, /sheets/access-summary, /sheets/{id}/audit (registrada antes que sheets)
  api/routes/bulk.py             POST /sheets/{id}/shares/copy, POST /users/{key}/revoke (simulación por defecto)
  core/config.py                 Settings (pydantic-settings) con token SecretStr, read_only, Host y Origin
  core/errors.py                 AppError(code, message, status) y manejador único
  core/middleware.py             OriginMiddleware: Origin permitido en escrituras
  models/sheets.py               SheetSummary, SheetList
  models/shares.py               Share, ShareList, Recipient, ShareCreate, ShareUpdate, ShareCreateResult
  models/people.py               Me, Person, PeopleResponse, PersonDetail, PersonSheetAccess, Group, Contact
  models/reports.py              SheetAudit, SheetComparison, AccessSummary
  models/bulk.py                 CopyRequest, RevokeRequest, BulkStep, CopyPlan, RevokePlan
  services/smartsheet/
    __init__.py                  API: SmartsheetClient y dataclasses
    client.py                    _request: auth, semáforo, reintentos, paginación (lastKey y page)
    errors.py                    respuesta de error de Smartsheet a AppError
    mappers.py                   JSON de Smartsheet a Raw*
    types.py                     RawSheet, RawShare, RawUser, RawGroup, RawContact, RawMe, NewShare, ShareMessage
  services/permissions/
    __init__.py                  API pública
    levels.py                    AccessLevel, ShareType, ShareScope, LockedReason, orden y etiquetas
    rules.py                     lock_reason, is_assignable, find_duplicates, share_sort_key
  services/cache.py              TtlCache con single flight, invalidación y loaded_at
  services/search.py             búsqueda sin tildes ni mayúsculas
  services/sheets.py             SheetService
  services/shares.py             ShareService: CRUD con modo solo lectura y reglas
  services/directory.py          build_directory: agregación pura de contactos, organización y permisos
  services/people.py             PeopleService: directorio, detalle, contactos, organización, grupos, me
  services/audit_rules.py        reglas puras de auditoría (tabla RULES) y dominios personales
  services/reports.py            ReportService: auditoría, comparación y resumen de acceso
  services/account_review.py     AccountReviewService: reglas de auditoría sobre toda la cuenta
  services/bulk_plans.py         planes puros: nivel efectivo, plan de copia, StepAction
  services/bulk.py               BulkService: copiar y revocar con simulación; ejecuta vía ShareService
```

## Flujo de lectura de permisos de una hoja

1. `GET /api/sheets/{sheet_id}/shares` llega a la ruta, que usa `ShareService`.
2. `ShareService.list` busca `shares:{sheet_id}` en la caché; si está vigente la devuelve.
3. Si no, `SmartsheetClient.list_sheet_shares` llama a `GET /shares?assetType=sheet&assetId={id}&sharingInclude=ITEM,WORKSPACE` y sigue `lastKey` hasta el final (ADR-B03).
4. `mappers` convierte cada elemento en `RawShare`; `permissions.can_edit_share` marca `editable` y `locked_reason` (propietario, heredado).
5. La ruta responde `Share[]` ordenado por nivel descendente y luego por nombre.

## Flujo de escritura

1. `POST`, `PATCH` o `DELETE` pasan `OriginMiddleware`: un Origin fuera de la lista recibe 403 antes de llegar a la ruta.
2. La ruta valida el cuerpo con Pydantic y llama a `ShareService`.
3. Si `APP_READ_ONLY=true`, 403 `READ_ONLY_MODE` y fin (ADR-B11).
4. `ShareService` lee el permiso actual (sin caché) y aplica `permissions.rules`; si la regla lo prohíbe, `AppError` con código y ninguna llamada de escritura a Smartsheet.
5. Llama a Smartsheet (`POST /shares`, `PATCH /shares/{id}`, `DELETE /shares/{id}` con `assetType=sheet&assetId`).
6. Invalida `shares:{sheet_id}` y `people`.
7. Responde el estado nuevo leído desde Smartsheet, no el supuesto.

## Contrato

- Detalle de campos y errores: `estilos/API.md`.
- Identificadores de Smartsheet: hojas con `int` de 64 bits, que en JSON viajan como texto (`"122469189898116"`) para que JavaScript no los redondee (ADR-B07). Shares con texto (`"AAACsZ4KFOeE"`).
- Niveles: `VIEWER`, `COMMENTER`, `EDITOR`, `EDITOR_SHARE`, `ADMIN`, `OWNER` (orden ascendente).

## Seguridad y recursos

- Host y Origin de la lista permitida: loopback por defecto, ampliable con `APP_ALLOWED_HOSTS` y `APP_ALLOWED_ORIGINS` (ADR-B08).
- Un único `httpx.AsyncClient` por proceso, creado en el ciclo de vida de la app, con plazo por solicitud.
- Concurrencia hacia Smartsheet acotada por un semáforo (`smartsheet_max_concurrency`); Smartsheet limita a 300 solicitudes por minuto por token.
- Logs sin token, sin cuerpos de respuesta y sin correos; sólo método, ruta de Smartsheet sin query, estado y duración.
