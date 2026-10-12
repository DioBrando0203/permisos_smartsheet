# SPEC-B02 Permisos de una hoja (CRUD)

Estado: implementada; escrituras reales sin verificar (PEN-07) y bloqueadas por el modo solo lectura
Código: `api/routes/shares.py`, `services/shares.py`, `services/permissions/`
Relacionadas: SPEC-B04, ADR-B03, ADR-B04, ADR-B05, ADR-B06

## Objetivo

Ver quién tiene acceso a una hoja y dar, cambiar o quitar ese acceso con reglas que impidan errores graves (perder el propietario, tocar permisos heredados).

## Fuente en Smartsheet (ADR-B03)

- Listar: `GET /2.0/shares?assetType=sheet&assetId={id}&sharingInclude=ITEM,WORKSPACE`. Respuesta `{"items": [...], "lastKey"?: "..."}`; cada elemento con `id`, `type` (`USER` o `GROUP`), `userId` o `groupId` (texto), `email`, `name` (puede faltar), `accessLevel`, `scope` (`ITEM` o `WORKSPACE`). Verificado el 2026-10-12.
- Uno: `GET /2.0/shares/{shareId}?assetType=sheet&assetId={id}`. Verificado el 2026-10-12.
- Crear: `POST /2.0/shares?assetType=sheet&assetId={id}&sendEmail={bool}` con un arreglo de `{email | groupId, accessLevel}` y opcionales `subject`, `message`, `ccMe`. Sin verificar con la cuenta (PEN-07).
- Cambiar: `PATCH /2.0/shares/{shareId}?assetType=sheet&assetId={id}` con `{accessLevel}`. Sin verificar (PEN-07).
- Quitar: `DELETE /2.0/shares/{shareId}?assetType=sheet&assetId={id}`. Sin verificar (PEN-07).
- Si las escrituras nuevas fallan al verificarlas, respaldo legado: `POST/PUT/DELETE /2.0/sheets/{id}/shares[/{shareId}]` (registrar en ADR-B03).

## Comportamiento

### Listar

1. `GET /api/sheets/{sheet_id}/shares` devuelve `ShareList` (`sheet_id`, `shares`, `loaded_at`).
2. Cada `Share` trae `editable` y, si no lo es, `locked_reason`: `OWNER` (es el propietario), `INHERITED` (viene del workspace) o `NO_PERMISSION` (el token no es `ADMIN` ni `OWNER` de la hoja).
3. Orden: nivel descendente (`OWNER` primero), luego grupos antes que usuarios, luego nombre o correo.
4. Una misma persona puede aparecer dos veces (propio y heredado). Se devuelven ambos; el frontend decide cómo agruparlos.

### Modo solo lectura

- Con `APP_READ_ONLY=true`, POST, PATCH y DELETE responden 403 `READ_ONLY_MODE` antes de cualquier llamada a Smartsheet (ADR-B11).

### Dar acceso

1. `POST /api/sheets/{sheet_id}/shares` con `ShareCreate`: `recipients` (1 a 50: `{email}` o `{group_id}`), `access_level`, `send_email` (por defecto `false`), `subject` y `message` opcionales (sólo si `send_email`).
2. Validación previa sin llamar a Smartsheet: correos con formato válido, sin duplicados (sin distinguir mayúsculas), `access_level` distinto de `OWNER`, el token puede administrar la hoja.
3. Un destinatario que ya tiene permiso propio en la hoja no se vuelve a crear: se informa en `skipped` con motivo `ALREADY_SHARED` y su nivel actual. Para cambiarlo se usa PATCH.
4. Respuesta `ShareCreateResult`: `created: Share[]` (leídos de Smartsheet tras crear) y `skipped: [{recipient, reason, current_level}]`.

### Cambiar nivel

1. `PATCH /api/sheets/{sheet_id}/shares/{share_id}` con `{access_level}`.
2. Se lee el permiso actual sin caché. Prohibido si es `OWNER`, si `scope=WORKSPACE`, si el nivel pedido es `OWNER` o si el token no administra la hoja.
3. Si el nivel pedido es igual al actual, responde el permiso sin llamar a Smartsheet.
4. Responde el `Share` actualizado.

### Quitar acceso

1. `DELETE /api/sheets/{sheet_id}/shares/{share_id}`.
2. Mismas prohibiciones que cambiar nivel (salvo el nivel pedido).
3. Responde 204. Un permiso que ya no existe responde 404 `SHARE_NOT_FOUND`.

### Después de escribir

- Invalidar `shares:{sheet_id}`, `sheets` y `users` en la caché (ADR-B06).

## Criterios de aceptación

- CA-01: listar mapea propios y heredados con `editable` y `locked_reason`. Prueba: `test_shares.py::test_list_marks_owner_and_inherited_as_locked`.
- CA-02: orden por nivel, tipo y nombre. Prueba: `test_permissions.py::test_share_sort_order`.
- CA-03: crear con `OWNER` responde 422 `OWNER_NOT_ASSIGNABLE` sin llamar a Smartsheet. Prueba: `test_shares.py::test_cannot_create_owner`.
- CA-04: crear omite a quien ya tiene permiso propio y crea al resto. Prueba: `test_shares.py::test_create_skips_existing_and_does_not_email_by_default`.
- CA-05: crear envía `sendEmail=false` por defecto y `subject`/`message` sólo con aviso. Prueba: `test_shares.py::test_create_skips_existing_and_does_not_email_by_default`.
- CA-06: cambiar o quitar al propietario responde 409 `OWNER_LOCKED`. Prueba: `test_shares.py::test_owner_share_is_locked`.
- CA-07: cambiar o quitar un heredado responde 409 `SHARE_INHERITED`. Prueba: `test_shares.py::test_inherited_share_is_locked`.
- CA-08: cambiar al mismo nivel no llama a Smartsheet. Prueba: `test_shares.py::test_same_level_is_noop`.
- CA-09: tras crear, cambiar o quitar, la siguiente lectura va a Smartsheet. Prueba: `test_shares.py::test_writes_invalidate_cache`.
- CA-10: token sin `ADMIN` ni `OWNER` en la hoja: 403 `CANNOT_MANAGE_SHARES`. Prueba: `test_shares.py::test_viewer_token_cannot_manage`.
- CA-11: un Origin no permitido recibe 403 en POST, PATCH y DELETE. Prueba: `test_security.py::test_foreign_origin_cannot_write`.
- CA-13: modo solo lectura bloquea las tres escrituras sin llamar a Smartsheet. Prueba: `test_shares.py::test_read_only_mode_blocks_every_write`.
- CA-12: crear, cambiar y quitar funcionan con la cuenta real en la hoja de prueba. Prueba: manual (PEN-07).

## Pendientes

- Cambiar el propietario de una hoja: fuera de alcance; se hace en Smartsheet (ADR-B04).
- Avisar por correo al cambiar o quitar: Smartsheet no lo ofrece en estos endpoints.
