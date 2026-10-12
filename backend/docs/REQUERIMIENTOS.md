# Requerimientos y cobertura

## Prioridad de uso

Pensado para el equipo que administra las hojas de Smartsheet de la cuenta. Debe poder responder en segundos "¿quién tiene acceso a esta hoja y con qué nivel?" y "¿a qué hojas tiene acceso esta persona?", y corregirlo desde el panel sin abrir Smartsheet hoja por hoja. Cada cambio debe ser explícito, confirmado y reversible a mano.

## Datos de la cuenta (verificados el 2026-10-12, sólo lectura)

- Dueño del token: administrador del sistema de la cuenta, con licencia y administrador de grupos.
- 100 hojas visibles con `includeAll=true`; todas con nivel `OWNER` para el dueño del token en la muestra revisada.
- 4 usuarios en la organización y 2 grupos.
- Una hoja de muestra tenía 12 permisos propios (`scope=ITEM`) y 1 heredado del workspace (`scope=WORKSPACE`).
- 44 contactos (`GET /2.0/contacts`: sólo `id`, `name`, `email`). Cruce con los permisos de las 100 hojas: 36 personas con acceso, 31 de ellas son contactos; 13 contactos no tienen acceso a ninguna hoja; 5 personas con acceso no están en contactos; los 4 usuarios de la organización tienen acceso. Ningún grupo tiene acceso. 857 permisos en total.
- Conclusión: contactos no es lo mismo que gente con acceso; es la libreta de direcciones del dueño del token. Se unifican en el directorio (ADR-B10).
- `GET /2.0/shares?assetType=sheet&assetId=…` y el legado `GET /2.0/sheets/{id}/shares` responden 200.

## Requisitos verificables

- RQ-01 Listar hojas: todas las hojas accesibles por el token, con nombre, nivel del token, enlace a Smartsheet, fecha de modificación y búsqueda por nombre (SPEC-B01).
- RQ-02 Ver permisos de una hoja: cada usuario o grupo con nombre, correo, nivel y origen (propio o heredado del workspace) (SPEC-B02).
- RQ-03 Dar acceso: uno o varios correos o grupos con un mismo nivel, sin correo de aviso por defecto y con mensaje opcional si se avisa (SPEC-B02).
- RQ-04 Cambiar nivel: de un permiso propio de la hoja, a cualquier nivel excepto `OWNER` (SPEC-B02).
- RQ-05 Quitar acceso: de un permiso propio de la hoja, salvo el del propietario (SPEC-B02).
- RQ-06 Protecciones: propietario y permisos heredados se muestran pero no se modifican; la API lo explica con un código (ADR-B04, ADR-B05).
- RQ-07 Vista por usuario: personas y grupos con acceso a alguna hoja, cuántas hojas y cuáles con qué nivel (SPEC-B03).
- RQ-08 Token seguro: sólo en `backend/.env`; nunca en respuestas, logs, docs ni pruebas (SM-01).
- RQ-09 Resiliencia: reintentos con espera ante 429 y 5xx de Smartsheet; errores traducidos a mensajes en español con código estable (SPEC-B04).
- RQ-10 Coherencia: tras una escritura, la respuesta y las lecturas siguientes reflejan el estado real de Smartsheet (caché invalidada).
- RQ-11 Acceso local: loopback por defecto; red local sólo con variables de entorno explícitas (ADR-B08).
- RQ-12 Pruebas: sin llamadas reales a Smartsheet en la suite; datos sintéticos.
- RQ-13 Directorio: contactos, personas con acceso y usuarios de la organización en una lista, con su origen marcado y cantidad de hojas (0 si no tiene acceso), para dar acceso a cualquiera (SPEC-B03).
- RQ-14 Modo solo lectura: con `APP_READ_ONLY=true` toda escritura responde 403 `READ_ONLY_MODE` sin llamar a Smartsheet (ADR-B11).
- RQ-15 Puertos propios: backend 8710 y frontend 5710.

## Límites honestos

- El panel actúa con los permisos del token: lo que el token no ve, el panel no lo ve.
- La vista por usuario lee los permisos de todas las hojas; con 100 hojas son unas 100 solicitudes a Smartsheet (limitadas por concurrencia y caché). La primera carga tarda; las siguientes usan la caché.
- Los cambios hechos directamente en Smartsheet aparecen en el panel cuando vence la caché (`cache_ttl_seconds`) o al pulsar actualizar.
- Sin login propio en la primera versión: cualquiera que abra el panel actúa como el administrador dueño del token. Por eso es local por defecto (PEN-08).
- No hay historial propio de cambios en la primera versión; Smartsheet conserva su propio registro de actividad (PEN-09).
- Workspaces (4), carpetas, reportes (136) y dashboards (39) quedan fuera del alcance inicial (PEN-10); la API sí los expone.
- La API de contactos de Smartsheet sólo permite leer (listar y ver uno): el panel no crea ni edita contactos. Dar acceso a un correo nuevo lo agrega como colaborador de esa hoja.

## Pendientes (backlog priorizado)

Cada pendiente se cita por su ID. Al tomar uno: crear o actualizar la spec con sus criterios de aceptación y mover aquí su estado.

Resumen al 2026-10-12:
- Terminadas: PEN-00, PEN-01, PEN-02, PEN-03, PEN-05.
- Parciales: PEN-04 (CRUD hecho y probado con Smartsheet simulado; escrituras reales bloqueadas por el modo solo lectura hasta PEN-07).
- Por hacer, en orden: PEN-06 (frontend), PEN-07 y PEN-13 cuando el usuario decida escribir; después PEN-08 a PEN-12.

### PEN-00 Documentación inicial

Prioridad: alta. Alcance: proyecto. Estado: terminada (2026-10-12).
Hecho: README, AGENTS, docs de backend y de frontend (reglas, patrones UI/UX, sistema visual, specs iniciales), `.env` con el token y `.gitignore`.

### PEN-01 Esqueleto del backend

Prioridad: alta. Alcance: backend. Estado: terminada (2026-10-12).
Hacer: `pyproject.toml`, `app/main.py`, `core/` (config con `SecretStr`, errores, middleware de Origin), `GET /api/health`, `GET /api/me`, Ruff y pytest configurados.
Terminado cuando: `GET /api/health` responde `{"status":"ok","smartsheet":"configured"}`; `/api/me` devuelve el dueño del token contra la cuenta real; la configuración no muestra el token en `repr`.

### PEN-02 Cliente de Smartsheet

Prioridad: alta. Alcance: backend. Estado: terminada (2026-10-12).
Hacer: SPEC-B04 completa: `_request`, reintentos, paginación por `lastKey` y por `page`, traducción de errores, semáforo, logs sin datos sensibles.
Terminado cuando: pruebas `respx` de éxito, 401, 403, 404, 429 con reintento, 500 con reintento y agotamiento de reintentos.

### PEN-03 Hojas

Prioridad: alta. Alcance: backend. Estado: terminada (2026-10-12).
Hacer: SPEC-B01 (`GET /api/sheets`, `GET /api/sheets/{id}`) con caché.
Terminado cuando: CA de SPEC-B01 con prueba y lectura real verificada (100 hojas).

### PEN-04 Permisos de una hoja (CRUD)

Prioridad: alta. Alcance: backend. Estado: parcial (2026-10-12): implementado y probado con Smartsheet simulado; falta PEN-07.
Hacer: SPEC-B02: listar, crear, cambiar y quitar; reglas puras en `permissions/`.
Terminado cuando: CA de SPEC-B02 con prueba; escrituras verificadas a mano en la hoja de prueba que designe el usuario y revertidas (PEN-07).

### PEN-05 Personas y grupos

Prioridad: alta. Alcance: backend. Estado: terminada (2026-10-12).
Hacer: SPEC-B03 (`GET /api/users`, `GET /api/users/{key}`, `GET /api/contacts`, `GET /api/groups`).
Terminado cuando: CA de SPEC-B03 con prueba; tiempo de la primera carga real anotado en RESULTADOS.

### PEN-06 Frontend

Prioridad: alta. Alcance: frontend. Estado: pendiente (empieza después de PEN-01 a PEN-05).
Hacer: specs SPEC-01 a SPEC-04 del frontend y su implementación con Fluent 2. El backend debe servir `frontend/dist` y devolver `index.html` en rutas que no sean `/api` ni `/assets` (ADR-04 del frontend).

### PEN-07 Verificación de escrituras reales

Prioridad: alta. Alcance: backend. Estado: pendiente; requiere decisión del usuario.
Situación: las escrituras de `/2.0/shares` (POST, PATCH, DELETE) sólo están documentadas, no verificadas con esta cuenta.
Hacer: el usuario designa una hoja de prueba y un correo de prueba; se crea, cambia y quita un permiso; se anota el resultado en BITACORA y se actualizan SPEC-B02 y SPEC-B04 si algo difiere.

### PEN-08 Acceso al panel con login

Prioridad: media. Alcance: backend y frontend. Estado: pendiente; requiere decisión.
Situación: sin login, quien abra el panel actúa como administrador.
Hacer: evaluar login con Smartsheet OAuth (cada persona actúa con sus propios permisos) o una contraseña compartida si sólo se usa en la red local. Exige ADR.

### PEN-09 Registro de cambios hechos desde el panel

Prioridad: media. Alcance: backend y frontend. Estado: pendiente.
Hacer: registro local (archivo JSONL rotado) de quién (cuando exista login), qué hoja, qué persona, nivel anterior y nuevo, y resultado. Exige ADR porque introduce persistencia.

### PEN-10 Workspaces y carpetas

Prioridad: media. Alcance: backend y frontend. Estado: pendiente.
Hacer: listar workspaces y administrar sus permisos (`assetType=workspace`), para poder corregir los permisos heredados que hoy son de sólo lectura.

### PEN-11 Operaciones masivas

Prioridad: baja. Alcance: backend y frontend. Estado: pendiente.
Hacer: quitar a una persona de todas sus hojas, copiar los permisos de una hoja a otras, cambiar el nivel de una persona en varias hojas. Con vista previa de cambios y confirmación; resultado por hoja (algunas pueden fallar).

### PEN-13 Crear usuario en la organización

Prioridad: media. Alcance: backend y frontend. Estado: pendiente; el usuario lo probará después.
Situación: dar acceso a un correo no lo vuelve usuario de la organización. `POST /2.0/users` lo agrega a la cuenta (puede consumir licencia y envía invitación).
Hacer: spec y ADR propios; confirmación reforzada; probar sólo con un correo de prueba designado por el usuario.

### PEN-14 Hojas de toda la organización

Prioridad: alta. Alcance: backend y frontend. Estado: pendiente.
Situación: `/sheets` sólo lista las 100 hojas propias o compartidas con el token; la organización tiene 104. Las 4 restantes son de otros usuarios y sus permisos sí se pueden leer como administrador del sistema (verificado 2026-10-12).
Hacer: listar con `GET /2.0/users/sheets` paginando por `page` (B-06), marcar `in_my_list` y el dueño, e incluirlas en el directorio. Escribir en ellas exige comprobar que Smartsheet lo permite al administrador (PEN-07).

### PEN-15 Última conexión de los usuarios

Prioridad: baja. Alcance: backend y frontend. Estado: pendiente.
Hacer: `GET /2.0/users?include=lastLogin` (verificado) para mostrar en el directorio cuándo entró por última vez cada usuario de la organización; útil para detectar accesos que sobran.

### PEN-12 Exportar

Prioridad: baja. Alcance: backend y frontend. Estado: pendiente.
Hacer: exportar a CSV la matriz persona por hoja con niveles. El archivo contiene correos reales: se genera bajo demanda y no se guarda en el servidor.
