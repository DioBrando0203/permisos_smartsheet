# Bloqueos y problemas conocidos (backend)

Formato: ID, fecha Lima, síntoma, causa, solución o prevención, estado.

## B-01 Escrituras de `/2.0/shares` sin verificar

Fecha: 2026-10-12. Estado: abierto (PEN-07).
Síntoma: POST, PATCH y DELETE de los endpoints unificados sólo están documentados.
Causa: no se escribe sobre hojas reales sin una hoja de prueba designada por el usuario.
Prevención: verificar en la hoja de prueba; si difieren, ajustar SPEC-B02 y ADR-B03 o usar los legados.

## B-02 `sharingInclude=ALL` no existe

Fecha: 2026-10-12. Estado: entendido.
Síntoma: 400 con `errorCode` 1018.
Causa: Smartsheet sólo acepta `ITEM`, `WORKSPACE` y `SUBJECT_DETAILS_PROFILE_IMAGE`, separados por coma.
Prevención: usar `sharingInclude=ITEM,WORKSPACE` (SPEC-B02).

## B-03 Nombre ausente en algunos permisos

Fecha: 2026-10-12. Estado: entendido.
Síntoma: un permiso de usuario llega sin `name`.
Causa: la persona no completó su perfil o es una invitación.
Prevención: `name` opcional en el contrato; el frontend muestra el correo como nombre.

## B-04 Token en un canal no seguro

Fecha: 2026-10-12. Estado: abierto; decide el usuario si rota el token.
Situación: el token se compartió en la conversación con el asistente para guardarlo en `backend/.env`.
Prevención: `.env` fuera del control de versiones; si hay duda de exposición, generar un token nuevo en Smartsheet y revocar el anterior.

## B-05 Mismo id para el permiso propio y el heredado

Fecha: 2026-10-12. Estado: entendido.
Síntoma: en una hoja real, el propietario aparece dos veces (`ITEM` y `WORKSPACE`) con el mismo `id` de permiso.
Causa: Smartsheet identifica el permiso por persona, no por origen.
Prevención: el frontend no puede usar `id` sola como clave de fila; usar `id` + `scope` (o agrupar por persona, UX-27). PATCH y DELETE actúan sobre el permiso propio y el backend comprueba el `scope` leído antes de escribir.

## B-06 `includeAll=true` no siempre trae todo

Fecha: 2026-10-12. Estado: abierto (PEN-14).
Síntoma: `GET /2.0/users/sheets?includeAll=true` devuelve 100 elementos con `totalPages=-1`, cuando con `pageSize=1000` hay 104.
Causa: ese endpoint no informa el total y corta en 100 pese a `includeAll`.
Prevención: para endpoints que respondan `totalPages=-1`, paginar por `page` hasta recibir menos de `pageSize`. Revisar `client._get_all` antes de usar `/users/sheets`. `/sheets`, `/contacts`, `/users` y `/groups` hoy devuelven totales coherentes.
