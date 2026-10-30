# Contrato con el backend (vista del frontend)

Fuente de verdad del JSON: `backend/docs/estilos/API.md`. Este documento dice cómo lo consume el frontend: hook, clave de caché, spec que lo usa e invalidaciones. Si difieren, gana `API.md` y se corrige aquí en el mismo cambio.

## Reglas del contrato

- K-01: todas las llamadas salen de `lib/api.ts` con rutas relativas `/api/...` (proxy de Vite en desarrollo, mismo origen en producción; ADR-07).
- K-02: ids siempre `string`; nunca `Number(id)` (ADR-B07 del backend).
- K-03: error del backend `{"detail": {"code", "message", "ref_id", "upstream_message"}}` se convierte en `ApiError` con `code`, `message`, `refId` y `status`. El texto visible sale de `lib/errorMessages.ts` por `code`; `message` del backend sólo como respaldo si el código no está en la tabla.
- K-04: errores de validación de FastAPI (422 con `detail` como lista) se convierten en `ApiError` con `code = "VALIDATION"`.
- K-05: sin respuesta (red caída o backend detenido): `ApiError` con `code = "BACKEND_UNREACHABLE"`.
- K-06: cada respuesta pasa por su función de `lib/normalize.ts`, que tolera campos ausentes (valores por defecto) y fechas ISO como `string` (se formatean al mostrar, no se convierten a `Date` en caché).
- K-07: `refresh=true` sólo lo envía el botón "Actualizar" de cada vista; el resto de lecturas usa la caché del backend (120 s).
- K-08: las escrituras sólo se intentan si `GET /api/health` devolvió `read_only: false`; si no, los controles se muestran deshabilitados con el motivo (UX-28).
- K-09: la exportación CSV es un enlace de descarga (`<a href download>`), no un `fetch`: el archivo no pasa por memoria de la app.

## Lecturas

Formato: método y ruta | hook | clave de caché | spec.

- `GET /api/health` | `useHealth` | `['health']` | SPEC-01. Sin reintentos; se consulta al arrancar y cada 60 s.
- `GET /api/me` | `useMe` | `['me']` | SPEC-01.
- `GET /api/sheets?scope=all` | `useSheets` | `['sheets']` | SPEC-02. Se pide una vez con `scope=all` y se filtra en el navegador por `q` y alcance (114 hojas).
- `GET /api/sheets/{id}` | `useSheet` | `['sheet', id]` | SPEC-05. Acepta id o código de permalink.
- `GET /api/sheets/{id}/shares` | `useShares` | `['shares', id]` | SPEC-03.
- `GET /api/users` | `usePeople` | `['people']` | SPEC-04. Una sola lectura; filtros `only` y `q` en el navegador. Primera carga lenta (3 a 5 s).
- `GET /api/users/{key}` | `usePerson` | `['person', key]` | SPEC-04. `key` codificada con `encodeURIComponent` (lleva `@`).
- `GET /api/contacts` | `useContacts` | `['contacts']` | SPEC-03 (autocompletado).
- `GET /api/groups` | `useGroups` | `['groups']` | SPEC-03 (autocompletado).
- `GET /api/sheets/{id}/audit` | `useSheetAudit` | `['audit', id]` | SPEC-05.
- `GET /api/sheets/{id}/activity?days&limit` | `useSheetActivity` | `['activity', id, days]` | SPEC-05.
- `GET /api/sheets/{id}/rows/{rowId}/history?column_id` | `useRowHistory` | `['rowHistory', id, rowId, columnId]` | SPEC-05. Sólo al abrir el detalle de una fila (puede tardar 10 s).
- `GET /api/sheets/{id}/automations` | `useSheetAutomations` | `['automations', id]` | SPEC-05.
- `GET /api/sheets/{id}/columns` | `useColumns` | `['columns', id]` | SPEC-05 y SPEC-09.
- `GET /api/sheets/{id}/quality?unique&required&pattern` | `useSheetQuality` | `['quality', id, params]` | SPEC-09. Sólo al pulsar "Revisar".
- `GET /api/sheets/{id}/references?column&catalog_sheet&catalog_column` | `useSheetReferences` | `['references', id, params]` | SPEC-09.
- `GET /api/references?column&catalog_sheet&catalog_column&q` | `useAccountReferences` | `['referencesAccount', params]` | SPEC-09.
- `GET /api/review?min_severity&q` | `useAccountReview` | `['review', minSeverity]` | SPEC-06.
- `GET /api/sheets/access-summary?q&inactive_days` | `useAccessSummary` | `['accessSummary', q, inactiveDays]` | SPEC-06.
- `GET /api/automations?only_problems&q` | `useAccountAutomations` | `['automationsAccount']` | SPEC-06. Primera carga lenta (unos 17 s).
- `GET /api/sheets/compare?a&b` | `useCompare` | `['compare', a, b]` | SPEC-07.
- `GET /api/designers?q&closed_status` | `useDesigners` | `['designers', params]` | SPEC-08. Primera carga lenta (unos 14 s).
- `GET /api/map/point?lat&lon` | `useMapPoint` | `['map-point', lat, lon]` | SPEC-11. `staleTime` 10 minutos.
- `GET /api/map/segment?start_lat&start_lon&end_lat&end_lon` | `useMapSegment` | `['map-segment', a, b]` | SPEC-11. `staleTime` 10 minutos.
- `GET /api/export/access.csv?q&scope` | enlace de descarga | sin caché | SPEC-02 y SPEC-04 (K-09).

## Escrituras

Todas exigen `read_only: false` (K-08) y son pesimistas (ADR-03).

- `POST /api/sheets/{id}/shares` | `useShareMutations().create` | SPEC-03.
- `PATCH /api/sheets/{id}/shares/{shareId}` | `useShareMutations().update` | SPEC-03.
- `DELETE /api/sheets/{id}/shares/{shareId}` | `useShareMutations().remove` | SPEC-03.
- `POST /api/sheets/{id}/shares/copy` | `useCopyShares` | SPEC-07. Con `dry_run: true` es una lectura (simulación) y se permite en modo solo lectura.
- `POST /api/users/{key}/revoke` | `useRevokePerson` | SPEC-04. Igual: la simulación se permite siempre.

## Invalidación tras una escritura real

- Dar, cambiar o quitar en la hoja `id`: `['shares', id]`, `['sheet', id]`, `['people']`, `['person']` (todas), `['audit', id]`, `['review']`, `['accessSummary']`, `['compare']`, `['designers']`.
- Copiar a la hoja destino: lo mismo con el destino.
- Quitar a una persona de varias hojas: lo mismo para cada hoja tocada.
- Una sola función, `invalidateAfterShareWrite(queryClient, sheetIds)` en `lib/query/invalidation.ts` (P-24).

## Códigos de error y texto visible (`lib/errorMessages.ts`)

Formato: código | texto | acción.

- `BACKEND_UNREACHABLE` | "No se puede conectar con el backend del panel." | "Inícielo con `python run.py` en `backend` y pulse Reintentar."
- `TOKEN_MISSING` | "Falta el token de Smartsheet en `backend/.env`." | Ninguna en la interfaz; guía en LEVANTAMIENTO.md.
- `SMARTSHEET_AUTH` | "Smartsheet rechazó el token." | "Genere uno nuevo en Smartsheet y actualice `backend/.env`."
- `SMARTSHEET_FORBIDDEN` | "Smartsheet no permite esta operación con la cuenta del panel." | Mostrar `upstream_message` si existe.
- `SMARTSHEET_RATE_LIMITED` | "Smartsheet está limitando las consultas." | "Espere un minuto y pulse Reintentar."
- `SMARTSHEET_UNAVAILABLE` | "Smartsheet no respondió." | "Reintentar."
- `SMARTSHEET_REJECTED` | "Smartsheet rechazó los datos." | Mostrar `upstream_message`.
- `READ_ONLY_MODE` | "El panel está en modo solo lectura: no se cambió nada." | Ninguna (no debería ocurrir: los controles ya están deshabilitados).
- `ORIGIN_NOT_ALLOWED` | "Esta dirección no está autorizada para hacer cambios." | "Abra el panel desde su dirección habitual."
- `CANNOT_MANAGE_SHARES` | "La cuenta del panel no es Administrador ni Propietario de esta hoja." | Ninguna.
- `NOT_SHARED_WITH_TOKEN` | "La hoja es de otra persona y no está compartida con la cuenta del panel: sólo se consulta." | Ninguna.
- `OWNER_LOCKED` | "El propietario no se cambia desde el panel." | "Hágalo en Smartsheet."
- `SHARE_INHERITED` | "Este acceso viene del workspace." | "Cámbielo en el workspace."
- `OWNER_NOT_ASSIGNABLE` | "No se puede dar el nivel Propietario." | Ninguna.
- `DUPLICATE_RECIPIENTS` | "Hay destinatarios repetidos." | Marcar los chips repetidos.
- `SHEET_NOT_FOUND` | "La hoja no existe o la cuenta del panel no tiene acceso." | Enlace a Hojas.
- `SHARE_NOT_FOUND` | "Ese acceso ya no existe; alguien lo cambió en Smartsheet." | "Actualizar."
- `PERSON_NOT_FOUND` | "No se encontró a esa persona." | Enlace a Personas.
- `ROW_NOT_FOUND`, `COLUMN_NOT_FOUND` | "La fila o columna ya no existe." | Mostrar sugerencias del `message` del backend en `COLUMN_NOT_FOUND`.
- `NO_CHECKS`, `TOO_MANY_COLUMNS`, `INVALID_PATTERN` | Texto del `message` del backend junto al campo. | Ninguna.
- `SAME_SHEET` | "Elija dos hojas distintas." | Ninguna.
- `VALIDATION` | "Algún dato no es válido." | Señalar el campo si se puede.
- Cualquier otro: `message` del backend o "Algo salió mal." con `ref_id` copiable (UX-18).
