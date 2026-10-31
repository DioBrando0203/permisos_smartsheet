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

- Fuera de `/api`: si existe `frontend/dist`, `/` y cualquier ruta del panel (`/hojas/...`) devuelven `index.html` y `/assets/...` los estáticos; `/docs`, `/redoc` y `/openapi.json` no se tapan; `/api/<inexistente>` sigue en 404.

- `GET /api/health`: `{"status": "ok", "smartsheet": "configured" | "missing_token", "read_only": bool}`. No llama a Smartsheet.
- `GET /api/me`: `Me` del dueño del token.
- `GET /api/sheets?q=&scope=&refresh=`: `SheetList`. `scope`: `all` (defecto: las del token y las de otras personas de la organización), `mine`, `org_only`.
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
- `GET /api/sheets/{sheet_id}/activity?days=30&limit=100&refresh=`: `SheetActivity` (SPEC-B08).
- `GET /api/sheets/{sheet_id}/rows/{row_id}/history?column_id=`: `RowHistory`.
- `GET /api/sheets/{sheet_id}/columns`: `ColumnInfo[]`.
- `GET /api/sheets/{sheet_id}/quality?unique=&required=&pattern=&refresh=`: `SheetQuality` (SPEC-B09); parámetros repetibles.
- `GET /api/export/access.csv?q=&scope=`: CSV para Excel (`;`, UTF-8 con BOM), una fila por permiso; cabecera `X-Failed-Sheets`; fórmulas neutralizadas con `'`.
- `GET /api/automations?q=&only_problems=&refresh=`: `AccountAutomations` (SPEC-B10).
- `GET /api/sheets/{sheet_id}/automations?refresh=`: `SheetAutomations`.
- `GET /api/sheets/{sheet_id}/references?column=&catalog_sheet=&catalog_column=&refresh=`: `SheetReferences` (SPEC-B11).
- `GET /api/references?column=&catalog_sheet=&catalog_column=&q=&refresh=`: `AccountReferences`.
- `GET /api/designers?q=&designer_columns=&status_column=&closed_status=&refresh=`: `DesignerWorkload` (SPEC-B12); valores por defecto desde `APP_DESIGNER_COLUMNS`, `APP_STATUS_COLUMN`, `APP_CLOSED_STATUSES`.
- `GET /api/map/point?lat=&lon=&radius_m=25&refresh=`: `MapPoint` (SPEC-B14); sólo Florida, radio de 1 a 200 m. `parcel.source` dice si la parcela vino de FDACS o del respaldo del condado (`broward_parcels`, sólo folio).
- `GET /api/map/segment?start_lat=&start_lon=&end_lat=&end_lon=&radius_m=25&refresh=`: `MapSegment` (SPEC-B14).
- `GET /api/map/search?q=&refresh=`: `MapSearch` (SPEC-B14); `q` de 3 a 120 caracteres: coordenadas, dirección, calle del FDOT o ruta con milepost (`SR 953 3.5`); hasta 8 resultados en Florida y el estado de cada fuente consultada.
- `GET /api/map/sources`: catálogo fijo `MapSource[]`; no consulta GIS.
- `POST /api/sheets/{sheet_id}/shares/copy`: cuerpo `CopyRequest`; `CopyPlan` (SPEC-B06). Simulación por defecto.
- `POST /api/users/{key}/revoke`: cuerpo `RevokeRequest`; `RevokePlan`. Simulación por defecto.
- Ejemplos en Swagger: plan 2026 `1842596423880580` (permalink `QMFVM7v3V23HqwgmCwHg5wF8XHFr5GCG4WJjXJF1`) y plan 2025 `5750050894335876`.
- `sheet_id`: id numérico o código del permalink (letras y dígitos, hasta 64); `share_id`: `[A-Za-z0-9_-]`. Otro valor responde 422 sin llamar a Smartsheet.

## Modelos

### Me

- `user_id`, `email`, `name`, `account_name`, `is_system_admin`.

### SheetSummary

- `id`, `name`, `access_level` (del token; `null` en hojas de otras personas no compartidas con el token), `can_manage_shares`, `permalink` y `modified_at` (`null` en esas hojas), `has_dynamic_view` (marca manual de `APP_DYNAMIC_VIEW_SHEETS`), `owner_email`, `in_my_list` (`false`: sólo consulta).

### SheetList

- `sheets`: `SheetSummary[]` filtradas por `q` y `scope`; `total`: todas sin filtrar; `total_mine`: las del token; `loaded_at`: hora de la lectura en caché.

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

- `key` (correo en minúsculas, `group-<id>` o `user-<id>` si falta el correo), `type`, `name`, `email`, `sheet_count` (0 si no tiene acceso), `highest_level` o `null`, `is_contact`, `is_org_member`, `is_token_owner`, `last_login` (sólo usuarios de la organización).

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

### SheetActivity

- `sheet`, `days`, `since`, `rows_total`, `changed_rows_total`.
- `changed_rows`: `[{row_id, row_number, label, created_at, created_by, modified_at, modified_by}]` (`created_by` y `modified_by`: `{email, name}`).
- `editors`: `[{email, name, rows_changed, last_change, access_level}]`; `access_level` `null` si ya no tiene la hoja compartida.
- `idle_editors`: `[{key, email, name, access_level}]` con `EDITOR` o superior sin filas modificadas en el período.
- `limitations`: textos; el primero avisa si una cuenta concentra más del 80 % de las filas.

### RowHistory

- `sheet_id`, `row_id`, `changes` (`[{column_id, column_title, value, modified_at, modified_by}]`, del más reciente), `columns_checked`, `failed_columns`.

### ColumnInfo y SheetQuality

- `ColumnInfo`: `id`, `title`, `type`, `index`, `primary`.
- `SheetQuality`: `sheet`, `rows_total`, `checks`: `[{column, column_id, check (unique|required|pattern), pattern, issues_count, issues: [{value, rows: [{row_id, row_number, label}]}], truncated}]`; hasta 200 filas por revisión en `issues`, `issues_count` siempre completo.

### SheetAutomations y AccountAutomations

- `Automation`: `id`, `name`, `enabled`, `status` (`ok`, `with_problems`, `disabled`), `action_type`, `frequency`, `recipient_emails`, `recipient_columns` (`[{id, title, type, is_contact, exists}]`), `notify_all_shared`, `smartsheet_reason`, `problems` (`[{code, message}]`: `DISABLED_NO_RECIPIENTS`, `DISABLED`, `NO_RECIPIENTS`, `RECIPIENT_COLUMN_MISSING`, `RECIPIENT_COLUMN_NOT_CONTACT`, `RECIPIENT_NOT_SHARED`), `modified_at`, `modified_by`.
- `SheetAutomations`: `sheet`, `counts` por estado, `automations`.
- `AccountAutomations`: `sheets_reviewed`, `sheets_with_rules`, `rules_total`, `by_status`, `by_problem`, `sheets` (`[{sheet_id, sheet_name, counts, problems}]`), `failed_sheets`.

### SheetReferences y AccountReferences

- `SheetReferences`: `sheet`, `column`, `catalog_sheet`, `catalog_column`, `catalog_values_count`, `checked_rows` (con valor), `missing_count`, `missing` (`QualityIssue[]` por valor, hasta 200 filas), `truncated`.
- `AccountReferences`: `column`, `catalog_sheet`, `catalog_column`, `catalog_values_count`, `sheets_checked`, `sheets_without_column`, `missing_total`, `by_value` (`[{value, sheets, rows}]`, el que falta en más hojas primero), `sheets` (`[{sheet_id, sheet_name, missing_count, missing_values}]`), `failed_sheets`.

### DesignerWorkload

- `designer_columns`, `status_column`, `closed_statuses`, `sheets_reviewed`, `sheets_with_designers`, `open_total`, `on_hold_total`, `closed_total`, `header_like_rows`, `failed_sheets`.
- `designers`: `[{name, in_catalog, person: {key, email, name} | null, ambiguous, open, on_hold, closed, by_phase, sheets_without_access, sheets: [{sheet_id, sheet_name, open, on_hold, closed, has_access, access_level}]}]`, más trabajo abierto primero.
- `sheet_gaps`: `[{sheet_id, sheet_name, open_without_designer, without_status}]`.

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
- 403 `NOT_SHARED_WITH_TOKEN`: escritura en una hoja de otra persona no compartida con el token (PEN-14).
- 403 `CANNOT_MANAGE_SHARES`: el token no es `ADMIN` ni `OWNER` de la hoja.
- 403 `SMARTSHEET_FORBIDDEN`: Smartsheet negó la operación.
- 404 `SHEET_NOT_FOUND`, `SHARE_NOT_FOUND`, `PERSON_NOT_FOUND`, `ROW_NOT_FOUND`, `COLUMN_NOT_FOUND`.
- 409 `OWNER_LOCKED`: cambiar o quitar al propietario.
- 409 `SHARE_INHERITED`: cambiar o quitar un permiso heredado del workspace.
- 422 `NO_CHECKS`, `TOO_MANY_COLUMNS`, `INVALID_PATTERN`: revisión de calidad mal pedida (SPEC-B09).
- 422 `SAME_SHEET`: comparar o copiar una hoja consigo misma.
- 422 `OWNER_NOT_ASSIGNABLE`: pedir el nivel `OWNER`.
- 422 `DUPLICATE_RECIPIENTS`: el mismo correo o grupo dos veces.
- 422 `COORDINATES_OUT_OF_FLORIDA`, `SEGMENT_ROADWAY_MISMATCH`, `SEGMENT_TOO_LONG`: consulta de mapa inválida.
- 422 `SMARTSHEET_REJECTED`: Smartsheet rechazó los datos (`upstream_message` explica).
- 502 `SMARTSHEET_AUTH`: token inválido, vencido o revocado.
- 502 `SMARTSHEET_UNAVAILABLE`: Smartsheet no respondió tras los reintentos.
- 503 `SMARTSHEET_RATE_LIMITED`: límite de solicitudes tras los reintentos.
- 503 `TOKEN_MISSING`: falta `SMARTSHEET_ACCESS_TOKEN`.
- 503 `GIS_DISABLED`: `APP_GIS_ENABLED=false`.
- 502 `GIS_UNAVAILABLE`: ninguna fuente vial o de límites respondió.
