# Contrato y estilo de API

Estado: implementado (2026-10-12). Se actualiza en el mismo cambio que `app/models/`. OpenAPI generado en `http://127.0.0.1:8710/docs`.

## Convenciones

- Rutas bajo `/api`, en inglés, minúsculas y plural (`/sheets/{sheet_id}/shares`).
- JSON `snake_case`, fechas ISO-8601 UTC, ids siempre como texto (ADR-B07).
- Niveles (`access_level`): `VIEWER`, `COMMENTER`, `EDITOR`, `EDITOR_SHARE`, `ADMIN`, `OWNER`.
- Errores propios: `{"detail": {"code": "CODIGO", "message": "texto en español", "ref_id": "…" | null, "upstream_message": "…" | null}}`.
- Errores de validación de FastAPI: 422 con `{"detail": [...]}` estándar.
- Nunca devolver el token, URLs de Smartsheet con query, trazas ni JSON crudo de Smartsheet.

## Endpoints

- `GET /api/health`: `{"status": "ok", "smartsheet": "configured" | "missing_token", "read_only": bool}`. No llama a Smartsheet.
- `GET /api/me`: `Me` del dueño del token.
- `GET /api/sheets?q=&refresh=`: `SheetList`.
- `GET /api/sheets/{sheet_id}`: `SheetSummary`.
- `GET /api/sheets/{sheet_id}/shares?refresh=`: `ShareList`.
- `POST /api/sheets/{sheet_id}/shares`: cuerpo `ShareCreate`; 201 con `ShareCreateResult`.
- `PATCH /api/sheets/{sheet_id}/shares/{share_id}`: cuerpo `ShareUpdate`; 200 con `Share`.
- `DELETE /api/sheets/{sheet_id}/shares/{share_id}`: 204.
- `GET /api/users?q=&only=&refresh=`: `PeopleResponse` (directorio). `only`: `contacts`, `org`, `external`, `groups`, `with_access`, `without_access`.
- `GET /api/users/{key}`: `PersonDetail`. `key` es el correo de la persona o `group-<id>`.
- `GET /api/contacts?refresh=`: `Contact[]` (libreta del dueño del token).
- `GET /api/groups?refresh=`: `Group[]`.
- `GET /api/sheets/{sheet_id}/audit?refresh=`: `SheetAudit` (SPEC-B05).
- `GET /api/sheets/compare?a=&b=`: `SheetComparison`; `a` y `b` id o código de permalink.
- `GET /api/sheets/access-summary?q=&inactive_days=&refresh=`: `AccessSummary`.
- `GET /api/review?q=&min_severity=&refresh=`: `AccountReview` (SPEC-B07); `min_severity` `high`, `medium` (defecto) o `info`.
- `POST /api/sheets/{sheet_id}/shares/copy`: cuerpo `CopyRequest`; `CopyPlan` (SPEC-B06). Simulación por defecto.
- `POST /api/users/{key}/revoke`: cuerpo `RevokeRequest`; `RevokePlan`. Simulación por defecto.
- Ejemplos en Swagger: plan 2026 `1842596423880580` (permalink `QMFVM7v3V23HqwgmCwHg5wF8XHFr5GCG4WJjXJF1`) y plan 2025 `5750050894335876`.
- `sheet_id`: id numérico o código del permalink (letras y dígitos, hasta 64); `share_id`: `[A-Za-z0-9_-]`. Otro valor responde 422 sin llamar a Smartsheet.

## Modelos

### Me

- `user_id`, `email`, `name`, `account_name`, `is_system_admin`.

### SheetSummary

- `id`, `name`, `access_level` (del token), `can_manage_shares`, `permalink`, `modified_at`, `has_dynamic_view` (marca manual de `APP_DYNAMIC_VIEW_SHEETS`).

### SheetList

- `sheets`: `SheetSummary[]` filtradas por `q`; `total`: cantidad sin filtrar; `loaded_at`: hora de la lectura en caché.

### ShareList

- `sheet_id`, `shares`: `Share[]` ordenados (SPEC-B02), `loaded_at`.

### Share

- `id`: id del permiso en Smartsheet.
- `type`: `USER` o `GROUP`.
- `user_id`, `group_id`: texto o `null` según el tipo.
- `email`: texto o `null` (los grupos no tienen).
- `name`: texto o `null` (Smartsheet lo omite si la persona no completó su perfil).
- `access_level`.
- `scope`: `ITEM` (propio de la hoja) o `WORKSPACE` (heredado).
- `editable`: booleano.
- `locked_reason`: `OWNER`, `INHERITED`, `NO_PERMISSION` o `null`.

### ShareCreate

- `recipients`: 1 a 50 elementos `{"email": "…"}` o `{"group_id": "…"}`.
- `access_level`: cualquiera salvo `OWNER`.
- `send_email`: booleano, por defecto `false`.
- `subject`: hasta 200 caracteres, opcional; sólo con `send_email`.
- `message`: hasta 2000 caracteres, opcional; sólo con `send_email`.

### ShareCreateResult

- `created`: `Share[]`.
- `skipped`: `[{"recipient": {...}, "reason": "ALREADY_SHARED", "current_level": "EDITOR"}]`.

### ShareUpdate

- `access_level`: cualquiera salvo `OWNER`.

### PeopleResponse

- `people`: `Person[]` filtradas; `total`: sin filtrar; `loaded_at`.
- `incomplete`: booleano.
- `failed_sheets`: `[{"sheet_id", "sheet_name", "code"}]`.

### Person

- `key` (correo en minúsculas, `group-<id>` o `user-<id>` si falta el correo), `type`, `name`, `email`, `sheet_count` (0 si no tiene acceso), `highest_level` o `null`, `is_contact`, `is_org_member`, `is_token_owner`.

### PersonDetail

- `person`: `Person`; `sheets`: `PersonSheetAccess[]` por nombre de hoja (puede haber dos de la misma hoja: propio y heredado).

### Contact

- `id`, `email`, `name` o `null`.

### PersonSheetAccess

- `sheet_id`, `sheet_name`, `share_id`, `access_level`, `scope`, `editable`, `locked_reason`.

### Group

- `id`, `name`, `description`, `member_count` o `null`.

### SheetAudit

- `sheet`, `total`, `by_level`, `by_scope`, `by_domain` (`domain`, `count`, `is_personal`), `org_known`, `external_count` (`null` si no se conoce la organización), `unnamed_count`, `not_in_contacts_count`.
- `alerts`: `[{code, severity, message, count, people: [{key, type, name, email, access_level}]}]`. Códigos: `EXTERNAL_CAN_SHARE` (high), `PERSONAL_EMAIL_CAN_EDIT` (medium), `UNNAMED` (info), `NOT_IN_CONTACTS` (info).

### SheetComparison

- `a`, `b` (`SheetSummary`), `only_in_a`, `only_in_b`, `level_differences` (`[{key, type, name, email, level_a, level_b}]`, nivel efectivo), `same_count`.

### AccessSummary

- `sheets`: `[{sheet_id, sheet_name, modified_at, share_count, editors_count, external_count, personal_email_count, is_inactive}]` (sin contar al propietario), `failed_sheets`.

### AccountReview

- `min_severity`, `totals` (`sheets_reviewed`, `sheets_with_alerts`, `people_by_code`), `sheets` (`[{sheet_id, sheet_name, has_dynamic_view, max_severity, alerts: {código: personas}}]`), `people` (`[{key, type, name, email, codes, sheet_count}]`), `failed_sheets`.

### CopyRequest y RevokeRequest

- `CopyRequest`: `source_sheet_id`, `upgrade_levels` (false), `include_inherited` (false), `dry_run` (true).
- `RevokeRequest`: `sheet_ids` (`null` = todas), `dry_run` (true).

### CopyPlan y RevokePlan

- `CopyPlan`: `source`, `target`, `dry_run`, `counts` por acción, `steps`.
- `RevokePlan`: `person`, `dry_run`, `counts`, `steps`.
- `BulkStep`: `action` (`CREATE`, `UPGRADE`, `KEEP`, `SKIP`, `REMOVE`), `status` (`planned`, `done`, `failed`, `not_applicable`), `key`, `type`, `name`, `email`, `sheet_id`, `sheet_name`, `share_id`, `current_level`, `new_level`, `reason` (`OWNER`, `INHERITED`, `NO_PERMISSION`, `SAME_OR_HIGHER`, `LOWER_LEVEL_KEPT`), `error_code`.

## Códigos de error

- 400: Host fuera de `APP_ALLOWED_HOSTS` (`TrustedHostMiddleware`).
- 403 `ORIGIN_NOT_ALLOWED`: escritura con Origin fuera de `APP_ALLOWED_ORIGINS`.
- 403 `READ_ONLY_MODE`: `APP_READ_ONLY=true`; ninguna escritura llega a Smartsheet (ADR-B11).
- 403 `CANNOT_MANAGE_SHARES`: el token no es `ADMIN` ni `OWNER` de la hoja.
- 403 `SMARTSHEET_FORBIDDEN`: Smartsheet negó la operación.
- 404 `SHEET_NOT_FOUND`, `SHARE_NOT_FOUND`, `PERSON_NOT_FOUND`.
- 409 `OWNER_LOCKED`: cambiar o quitar al propietario.
- 409 `SHARE_INHERITED`: cambiar o quitar un permiso heredado del workspace.
- 422 `SAME_SHEET`: comparar o copiar una hoja consigo misma.
- 422 `OWNER_NOT_ASSIGNABLE`: pedir el nivel `OWNER`.
- 422 `DUPLICATE_RECIPIENTS`: el mismo correo o grupo dos veces.
- 422 `SMARTSHEET_REJECTED`: Smartsheet rechazó los datos (`upstream_message` explica).
- 502 `SMARTSHEET_AUTH`: token inválido, vencido o revocado.
- 502 `SMARTSHEET_UNAVAILABLE`: Smartsheet no respondió tras los reintentos.
- 503 `SMARTSHEET_RATE_LIMITED`: límite de solicitudes tras los reintentos.
- 503 `TOKEN_MISSING`: falta `SMARTSHEET_ACCESS_TOKEN`.
