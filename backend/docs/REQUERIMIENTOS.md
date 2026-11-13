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
- RQ-15 Puertos propios: backend 8710 y frontend 5710; `python run.py` (desde `backend`, con el entorno activado) arranca sin escribir el puerto y usa uno libre si el 8710 está ocupado (ADR-B14).
- RQ-16 Auditoría y comparación: alertas por hoja, diferencias entre dos hojas y resumen de acceso por hoja, sin escribir (SPEC-B05).
- RQ-20 Calidad de datos: repetidos, vacíos y formato en las columnas elegidas de una hoja (SPEC-B09).
- RQ-21 Exportar: CSV para Excel de quién tiene acceso a qué hoja (PEN-12).
- RQ-22 Toda la organización: hojas de otras personas visibles y de sólo consulta (PEN-14).
- RQ-23 Automatizaciones: estado y problemas de alertas y flujos de Smartsheet por hoja y en toda la cuenta (SPEC-B10).
- RQ-24 Referencias: valores de una columna que no están en una hoja catálogo, por hoja y en toda la cuenta (SPEC-B11).
- RQ-25 Carga de diseñadores: trabajo abierto, en espera y cerrado por diseñador y fase, y si tiene acceso a sus hojas (SPEC-B12).
- RQ-26 Mapa: de un punto, la vía con su milepost, de quién es la calle, ciudad, condado, ZIP y parcela; de un tramo, la vía con milepost inicial y final listos para OSP. Sólo lectura de servicios GIS públicos (SPEC-B14, PEN-29).
- RQ-19 Actividad: filas modificadas por período, quién edita, editores sin cambios e historial por fila o celda, directo de Smartsheet (SPEC-B08).
- RQ-18 Revisión de cuenta: alertas de todas las hojas agregadas por hoja y por persona (SPEC-B07).
- RQ-17 Operaciones masivas: copiar permisos entre hojas y quitar a una persona de varias hojas, con simulación por defecto (SPEC-B06).

## Límites honestos

- El panel actúa con los permisos del token: lo que el token no ve, el panel no lo ve.
- La vista por usuario lee los permisos de todas las hojas; con 100 hojas son unas 100 solicitudes a Smartsheet (limitadas por concurrencia y caché). La primera carga tarda; las siguientes usan la caché.
- Los cambios hechos directamente en Smartsheet aparecen en el panel cuando vence la caché (`cache_ttl_seconds`) o al pulsar actualizar.
- Sin login propio en la primera versión: cualquiera que abra el panel actúa como el administrador dueño del token. Por eso es local por defecto (PEN-08).
- No hay historial propio de cambios en la primera versión; Smartsheet conserva su propio registro de actividad (PEN-09).
- Actividad: el "Registro de actividad" de la web no tiene API (404) y Event Reporting no está en el plan (403); sólo se ve la última modificación de cada fila y el historial de cada celda. Una automatización que toca todas las filas tapa a los demás editores (SPEC-B08).
- Workspaces (4), carpetas, reportes (136) y dashboards (39) quedan fuera del alcance inicial (PEN-10); la API sí los expone.
- Dynamic View (complemento de pago de Smartsheet) comparte filas y columnas filtradas de una hoja sin compartir la hoja. Según la comunidad de Smartsheet no tiene API pública: las personas que sólo acceden por una vista dinámica no aparecen en el panel. "Quién tiene acceso" en el panel significa "quién tiene la hoja compartida" (B-07).
- La API de contactos de Smartsheet sólo permite leer (listar y ver uno): el panel no crea ni edita contactos. Dar acceso a un correo nuevo lo agrega como colaborador de esa hoja.

## Pendientes (backlog priorizado)

Cada pendiente se cita por su ID. Al tomar uno: crear o actualizar la spec con sus criterios de aceptación y mover aquí su estado.

Resumen al 2026-11-04 (actualizado el 2026-11-12 para PEN-27 y PEN-42 a PEN-47; estado de la hoja en `HOJA_PROJECT_KMV.md`):
- Terminadas: PEN-00 a PEN-03, PEN-05, PEN-12, PEN-14 a PEN-16, PEN-23, PEN-25, PEN-31, PEN-32, PEN-34 a PEN-41 y PEN-42; PEN-30 y PEN-33 en los condados que indican.
- En curso: PEN-24 (ID Manager y selector de Linked Tracking en operación en Pruebas), PEN-06 (frontend por fases), PEN-27 (catálogo de estados y vista por `Closed`; falta aprobar la clasificación), PEN-28 y PEN-29.
- Parciales: PEN-04 y PEN-11 (falta PEN-07), PEN-17, PEN-18 y PEN-21.
- Requieren decisión del usuario: PEN-07, PEN-08, PEN-13, PEN-43 (reparto de estados por equipo). Decidida, por planificar: PEN-45 (una maestra por año; con 140 columnas un año ya no entra: falta decidir qué columnas quitar). Sin empezar: PEN-09, PEN-10, PEN-19 y PEN-20. Propuesta: PEN-26. En curso: PEN-44 (separación por cliente: vista restringida por `Client Access`, reporte KMV - Customers y aviso `Client | Status Update`; falta probar la vista con otra cuenta y el primer envío real). Nuevas, por decidir el plan: PEN-48 (hoja de trabajo PROJECT KMV 1.0.0) y PEN-49 (hojas hijas de Records y Facturación). Implementada y comprobada en Pruebas: PEN-47 (Tracking Project cambia con Customer). En uso en Pruebas: PEN-46 (conversaciones compiladas en Obs). Bloqueada por el plan: PEN-22.

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

Prioridad: alta. Alcance: frontend y backend. Estado: en curso: F0 terminada; F1 a F3 en curso desde 2026-10-28 y F7 (mapa) terminada en su fase base (`frontend/docs/PLAN_IMPLEMENTACION.md`).
Hacer: fases F0 a F6 de `frontend/docs/PLAN_IMPLEMENTACION.md` con SPEC-01 a SPEC-09 del frontend. F0 incluye en el backend: servir `frontend/dist` con respaldo a `index.html` (ADR-04 del frontend), escribir `backend/.port` desde `run.py` (ADR-07), un Smartsheet falso para E2E (ADR-10) y dejar una sola etiqueta en `/api/review`.

### PEN-07 Verificación de escrituras reales

Prioridad: alta. Alcance: backend. Estado: pendiente; requiere decisión del usuario.
Situación: las escrituras de `/2.0/shares` (POST, PATCH, DELETE) sólo están documentadas, no verificadas con esta cuenta.
Hacer: el usuario designa una hoja de prueba y un correo de prueba; se crea, cambia y quita un permiso; se anota el resultado en BITACORA y se actualizan SPEC-B02 y SPEC-B04 si algo difiere.

### PEN-08 Acceso al panel con login

Prioridad: media. Alcance: backend y frontend. Estado: pendiente; requiere decisión.
Situación: sin login, quien abra el panel actúa como administrador.
Hacer: evaluar login con Smartsheet OAuth (cada persona actúa con sus propios permisos) o una contraseña compartida si sólo se usa en la red local. Exige ADR.
Trazabilidad (explicado al usuario el 2026-10-12): con el token actual, Smartsheet registra todo cambio a nombre del dueño del token. Si otras personas van a escribir desde el servicio, OAuth es el camino: cada una entra con su cuenta de Smartsheet (también colaboradores gratuitos), sin crear usuarios nuevos, y el historial queda a su nombre. `Assume-User` sólo sirve con usuarios de la organización (4).

### PEN-09 Registro de cambios hechos desde el panel

Prioridad: media. Alcance: backend y frontend. Estado: pendiente.
Hacer: registro local (archivo JSONL rotado) de quién (cuando exista login), qué hoja, qué persona, nivel anterior y nuevo, y resultado. Exige ADR porque introduce persistencia.

### PEN-10 Workspaces y carpetas

Prioridad: media. Alcance: backend y frontend. Estado: pendiente.
Hacer: listar workspaces y administrar sus permisos (`assetType=workspace`), para poder corregir los permisos heredados que hoy son de sólo lectura.

### PEN-11 Operaciones masivas

Prioridad: baja. Alcance: backend y frontend. Estado: parcial (2026-10-12): backend con simulación (SPEC-B06); falta ejecución real (PEN-07) y frontend.
Hacer: quitar a una persona de todas sus hojas, copiar los permisos de una hoja a otras, cambiar el nivel de una persona en varias hojas. Con vista previa de cambios y confirmación; resultado por hoja (algunas pueden fallar).

### PEN-13 Crear usuario en la organización

Prioridad: media. Alcance: backend y frontend. Estado: pendiente; el usuario lo probará después.
Situación: dar acceso a un correo no lo vuelve usuario de la organización. `POST /2.0/users` lo agrega a la cuenta (puede consumir licencia y envía invitación).
Hacer: spec y ADR propios; confirmación reforzada; probar sólo con un correo de prueba designado por el usuario.

### PEN-14 Hojas de toda la organización

Prioridad: alta. Alcance: backend y frontend. Estado: terminada (2026-10-16).
Situación: `/sheets` sólo lista las 100 hojas propias o compartidas con el token; la organización tiene 104. Las 4 restantes son de otros usuarios y sus permisos sí se pueden leer como administrador del sistema (verificado 2026-10-12).
Hacer: listar con `GET /2.0/users/sheets` paginando por `page` (B-06), marcar `in_my_list` y el dueño, e incluirlas en el directorio. Escribir en ellas exige comprobar que Smartsheet lo permite al administrador (PEN-07).

### PEN-15 Última conexión de los usuarios

Prioridad: baja. Alcance: backend y frontend. Estado: terminada (2026-10-16).
Hacer: `GET /2.0/users?include=lastLogin` (verificado) para mostrar en el directorio cuándo entró por última vez cada usuario de la organización; útil para detectar accesos que sobran.

### PEN-16 Auditoría y comparación de hojas

Prioridad: alta. Alcance: backend. Estado: terminada (2026-10-12).
Hecho: SPEC-B05 con la hoja de ejemplo del usuario (plan Crown Castle 2026): alertas, comparación con 2025 y resumen de los planes 2019 a 2026.

### PEN-17 Accesos por Dynamic View

Prioridad: media. Alcance: proyecto. Estado: parcial (2026-10-12): marca manual `APP_DYNAMIC_VIEW_SHEETS` y campo `has_dynamic_view`; falta que el usuario indique qué hojas la usan y el aviso en el frontend.
Situación: el panel no ve vistas dinámicas (sin API pública, B-07). Quien sólo entra por una vista no figura en ninguna lista del panel.
Hacer: confirmar con el usuario si la cuenta usa Dynamic View y en qué hojas; si sí, indicarlo en la interfaz (aviso por hoja marcada a mano) y revisar periódicamente si Smartsheet publica una API.

### PEN-18 Alertas automáticas

Prioridad: media. Alcance: backend. Estado: parcial (2026-10-12): la revisión de cuenta (SPEC-B07) está hecha; falta la tarea programada y el canal de aviso.
Hacer: tarea periódica que ejecuta la revisión, la compara con la anterior y avisa sólo de lo nuevo (persona externa que ahora puede compartir, correo personal nuevo con edición). Decidir con el usuario el canal (correo, Slack u otro) y dónde guardar la revisión anterior (exige ADR: rompe "sin persistencia").

### PEN-19 Accesos con vencimiento

Prioridad: media. Alcance: backend y frontend. Estado: pendiente.
Hacer: registrar "acceso hasta fecha" por persona y hoja y quitarlo automáticamente al vencer, con aviso previo. Exige persistencia (ADR) y escrituras reales (PEN-07).

### PEN-20 Plantillas de equipo por cliente

Prioridad: baja. Alcance: backend y frontend. Estado: pendiente.
Hacer: definir una vez un equipo con niveles por persona y aplicarlo a hojas nuevas con simulación (reutiliza SPEC-B06). Alternativa nativa: grupos de Smartsheet.

### PEN-21 Actividad de las hojas

Prioridad: media. Alcance: backend y frontend. Estado: parcial (2026-10-16): backend hecho (SPEC-B08); falta frontend.
Situación: el plan no incluye Event Reporting (B-08). Disponible: última modificación por fila (`include=writerInfo`) e historial por celda.
Hacer: `GET /api/sheets/{id}/activity` con las filas modificadas recientemente (quién y cuándo) y detalle por celda bajo demanda; resumen por hoja de quién editó en los últimos N días, cruzado con sus permisos (por ejemplo, editores que no editan desde hace meses). Complementa, no reemplaza, el registro propio de cambios del panel (PEN-09).

### PEN-22 Registro de eventos (si se contrata Event Reporting)

Prioridad: media. Alcance: backend y frontend. Estado: bloqueado por el plan (B-08).
Situación: con el complemento, `GET /2.0/events` da hasta 6 meses de acciones de toda la organización: quién compartió o quitó accesos, borró filas, abrió hojas, inició sesión.
Hacer: confirmar en el Admin Center o con Smartsheet si se contrata; si sí, leer `/events` paginando por `streamPosition`, filtrar por hoja y por persona, y usarlo como fuente principal de PEN-09, PEN-18 y PEN-21.

### PEN-23 Paginación explícita en el cliente

Prioridad: alta. Alcance: backend. Estado: terminada (2026-10-16).
Tipo (ADR-B15): mejora interna; evita que el panel deje de funcionar cuando Smartsheet retire `includeAll`.
Hacer: `_get_all` con `page` y `pageSize` en vez de `includeAll` (B-09, B-06); pruebas con varias páginas y con `totalPages=-1`.

### PEN-24 Servicios propios sobre Smartsheet (propuesta, requiere decisión)

Prioridad: media. Alcance: proyecto. Estado: en curso (2026-11-04): ID Manager en operación automática en Pruebas (procesador cada 60 s, sólo en el equipo Linux, B-16) y Linked Tracking vinculado a la hoja catálogo (SPEC-B16). OAuth no es requisito del piloto (SPEC-ID01 ID-29); PEN-08 sigue aplicando al panel. Resaltado en rojo del error de cliente hecho (LB-16). Pendientes: confirmar el filtrado al escribir el código del cliente, decidir qué hacer con la fila `PRUEBA - catálogo automático` y revisar al final la separación entre `APP_READ_ONLY` y las barreras del ID Manager (ID-36).
Contexto: el usuario evalúa Jira y Salesforce por sus conectores de pago. Smartsheet sigue como fuente de verdad; nuestro servicio sólo agrega lo que no da bien.
Plan futuro: IDs permanentes, catálogos, selectores por cliente, validación y supervisión en un servicio Windows; PostgreSQL con estado mínimo de asignación de IDs, sin replicar datos de negocio (ADR-B18). Fases y límites: `future_docs/SERVICIOS_SMARTSHEET_BD.md`; esquema e instalación: `servicios/ids/`. El panel actual conserva ADR-B02 y el modo solo lectura.
Prioridad actual: ID Manager, luego catálogo basado en Proyectos (Piloto) y validaciones; reutilizar capacidades nativas de Smartsheet cuando cumplan el requisito. DRY_RUN, coordinador, recuperación, adaptador con relectura y procesador probados con simulaciones y en Pruebas; migración 003 aplicada y política de numeración aprobada (SPEC-ID01 ID-32 a ID-36).
Avance 2026-11-11 09:32 -05:00: faltaba la referencia `Project Status Catalog Closed` (la API listaba sólo `Phase` y `Status`), por lo que `Closed` devolvía siempre falso sin error por el `IFERROR`. Creada por API (`POST /sheets/{id}/crosssheetreferences`, sí existe) apuntando a la columna `Closed` del catálogo. Prueba en la fila 8 vacía de PROJECT KMV: `4. Permit is Required` abierto, `COMPLETE` cerrado, `4. Permit Approved` abierto, `4. Permit Expired` cerrado, vacío abierto; fila restaurada. Falta en la interfaz: filtro de la Dynamic View por `Closed` sin marcar. Avance 2026-11-11 01:04 -05:00: agregadas a `PROJECT KMV` las columnas de fórmula `Phase` y `Closed` (INDEX/MATCH contra `Project Status Catalog`), confirmado funcionando con captura del usuario (ej. fase vacía en filas `IN PERMITTING`, fase 9 en `9. Permit Reopening`, fase 4 en `4. Permit is Required`, `Closed` sin marcar donde corresponde). Las 3 referencias entre hojas quedaron creadas a mano por el usuario en Smartsheet (Sheet Reference Manager, no hay API para crearlas): `Project Status Catalog Phase`, `Project Status Catalog Status` y `Project Status Catalog Closed`, cada una apuntando a la columna completa correspondiente. Fórmulas usadas — `Phase`: `=IFERROR(INDEX({Project Status Catalog Phase}, MATCH([Project Status]@row, {Project Status Catalog Status}, 0)), "")`; `Closed`: `=IFERROR(INDEX({Project Status Catalog Closed}, MATCH([Project Status]@row, {Project Status Catalog Status}, 0)), false)`. Falta aparte (sin API, manual en Smartsheet): armar el filtro de la Dynamic View sobre `Closed` (puede quedar oculta, sólo como filtro) y opcionalmente `Phase` si se quiere filtrar/agrupar por etapa; sigue pendiente la aprobación de la jefa de la clasificación (PEN-27: `4. Permit Approved` y `6. Permit - MOT Approved` quedaron como abiertos, fase 9 como reapertura, criterio de Claude pendiente de validar) y replicar el patrón en las tres hojas de cliente si se decide extenderlo ahí (ver `kmv-client-sheets-structure` en memoria).
Avance 2026-11-10 20:49 -05:00: creada `Project Status Catalog` en `/Pruebas/Producto` (hoja `PROJECT KMV`, la llamada "Presentable" en esta bitácora; no existe ninguna hoja con ese nombre literal) con columnas `Status`, `Phase` y `Closed`, y cargadas 61 filas con una clasificación propuesta de los ~80 valores de `Project Status` (fase 1-9 extraída del prefijo, cerrado/abierto por fase) para que el usuario la lleve a su jefa; quedan fuera a propósito los valores basura vistos como dato real en las tres hojas de cliente (el texto literal `"Project Status"` y los separadores `"----"`). Objetivo: que `Permitting Team` y `Permit Coordinator` (mismo rol) filtren su Dynamic View por una columna calculada (`Closed`) en vez del texto crudo de `Project Status`, para que la fila desaparezca sola al cambiar de estado (PEN-27 sigue abierto: confirmar con el usuario `4. Permit Approved` y `6. Permit - MOT Approved` como abiertos, y fase 9 como reapertura). Aún falta: aprobación de la jefa, columnas de fórmula `Phase`/`Closed` en `PROJECT KMV` con INDEX/MATCH contra el catálogo, y el filtro en la Dynamic View real.
Avance 2026-11-10 10:00 -05:00: el ID Manager pasa a la hoja Presentable (madres con ID, hijas con el ID de su madre; hojas anteriores olvidadas); reinicio a 001 hecho (2026-11-10 10:07 -05:00): registro vacío, Stable IDs de Presentable vaciados, catálogo limpio y `Control Linked Tracking` agregada; backend encendido por el usuario y ejemplo asignado (2026-11-10 10:14 -05:00): 4 madres 001/002 y 3 hijas con el ID de su madre, catálogo con 4 proyectos. Linked Tracking de Presentable vinculado al catálogo por el usuario y verificado (2026-11-10 10:20 -05:00). Pendiente: confirmar la regla roja con una prueba de cliente distinto (SPEC-ID01 ID-37 a ID-40, SPEC-B16 LB-18 y LB-19). Avance 2026-11-05 00:09 -05:00: el usuario creó el formato condicional rojo de Linked Tracking y confirmó que funciona (LB-16). Avance 2026-11-04 19:33 -05:00: verificación desde el equipo Windows, sólo lectura: catálogo con 16 proyectos y plan sin cambios; las 29 filas con ID del piloto tienen Stable ID igual al visible; una fila `other_customer` (la de LB-13). Avance 2026-11-04 17:31: el usuario eligió un proyecto de otro cliente; lo detectan la fórmula y el backend; falta el resaltado en rojo (LB-13, LB-14). Avance 2026-11-04 17:24: desplegable vinculado y prueba de punta a punta (LB-11, LB-12). Avance 2026-11-04 17:07 -05:00: hoja catálogo creada en Pruebas y sincronizada (11 proyectos); falta vincular Linked Tracking en la vista de tabla y comprobar el filtro en la interfaz (SPEC-B16 LB-08 a LB-10). Avance 2026-11-04 16:56: selectores de Linked Tracking (SPEC-B16): capacidades nativas verificadas (desplegables vinculados con filtro estático; dependientes por fila no disponibles); catálogo, validación y sincronización de hoja catálogo implementados y probados sin escrituras. Pendiente: crear la hoja catálogo y vincular el desplegable, con autorización. Avance 2026-11-04 16:36: política de numeración del usuario (la fórmula propone, el servicio conserva; SPEC-ID01 ID-32 a ID-35) y primera escritura real en Pruebas: cuatro IDs confirmados, repetición idempotente. Pendiente: decidir la activación permanente del procesador (ID-36). Avance 2026-11-04 15:29: migración 003 aplicada y reconocida; coordinador conectado al adaptador real, recuperación, procesador de asignación (deshabilitado por defecto) y diez endpoints en Swagger, probados con simulación y en lectura real. OAuth no es requisito del piloto por decisión del usuario (SPEC-ID01 ID-29). Pendientes: autorizar y ejecutar la prueba real (`servicios/ids/README.md`) y decidir el riesgo de numeración por fórmulas (ID-31). Antes: seis consultas de IDs autenticadas en Swagger; simulación y monitoreo opcional sin escrituras; adaptador y prueba manual preparados con barreras y exclusión por hoja. Pendientes: ejecutar 003 con respaldo/restauración, aprobar consecutivos por ámbito y prueba real, OAuth conforme PEN-08 y conexión del procesador de escritura. La API no garantiza atomicidad frente a cambios externos.
Política aprobada 2026-11-04: año de proyecto desde `Date Received`, secuencia por empresa/cliente/año; 2027 en adelante empieza en 001 y las secuencias existentes continúan, sin reiniciar 2026. Tareas por proyecto, Records y revisiones por tarea. Ámbitos históricos sin secuencia requieren inicio explícito; no se conoce todo el historial eliminado.
Procesador secuencial conectado al monitor automático desde 2026-11-04 16:48 (ID-36), sin OAuth por decisión del usuario (ID-29). DRY_RUN detecta proyectos nuevos antes de que aparezca su fórmula.
Opciones, de menor a mayor esfuerzo:
- Validación de datos: hecha (SPEC-B09 y SPEC-B11, 2026-10-16): repetidos, vacíos, formato y referencias contra una hoja catálogo. No hay hoja maestra de Record IDs; el catálogo verificado es "Source Designers".
- Bandeja personal por persona (sus filas asignadas en todas las hojas), con login OAuth para que cada cambio quede a su nombre. Cubre parte de Dynamic View y de la vista "mis tareas" de Jira.
- Registro de cambios en vivo con webhooks (disponibles en el plan): cada cambio de fila o celda en las hojas elegidas, guardado por nuestro servicio. Suple en parte Event Reporting (no ve permisos ni accesos). Exige una URL pública HTTPS y persistencia.
- Tiempo en cada estado y tareas atascadas (al estilo de Jira), calculado con ese registro.
Fuera de alcance: reemplazar Jira (tableros, flujos, SLA completos) o un CRM (ADR-B15). Cada opción debe ser algo que Smartsheet no tiene, o que tiene pero aquí es mejor, sin entorpecer el trabajo actual.

### PEN-25 Salud de las automatizaciones

Prioridad: alta. Alcance: backend y frontend. Estado: terminada (2026-10-16): SPEC-B10.
Tipo (ADR-B15): Smartsheet no avisa que sus alertas están apagadas o sin destinatarios; el panel sí. No cambia nada en las hojas.
Situación: 80 reglas en 63 hojas; sólo 9 funcionan; 56 apagadas a mano, 15 por Smartsheet, 16 sin destinatarios; ninguna avisa de asignaciones de diseñador.
Hacer: `GET /api/automations` (toda la cuenta) y `GET /api/sheets/{id}/automations`: regla, estado, motivo, acción, destinatarios y columnas de responsable que no son de tipo contacto. Reactivar o corregir una regla sería una escritura (PEN-07).

### PEN-26 Asignación desde el panel (propuesta)

Prioridad: media. Alcance: backend y frontend. Estado: propuesta; exige OAuth (PEN-08) y escrituras reales (PEN-07).
Tipo (ADR-B15): Smartsheet ya asigna; el panel sólo vale si es mejor: asignar muchas filas a la vez con vista previa y ver la carga de cada diseñador antes de asignar. Escribe en la misma columna de Smartsheet, así sus automatizaciones siguen funcionando.

### PEN-27 Estados cerrados confirmados por el usuario

Prioridad: media. Alcance: configuración en Smartsheet y backend. Estado: en curso (2026-11-11 16:45 -05:00); falta la aprobación de la clasificación.
Situación: `APP_CLOSED_STATUSES` usa una lista inicial supuesta. En la cuenta real la fase 4 (Permit) concentra el trabajo "abierto"; si estados como "4. Permit Approved" significan trabajo terminado para el diseñador, la carga está inflada.
Hecho (2026-11-11): `Project Status Catalog` (6541648290074500, `Pruebas/Producto`, 60 estados, sólo su propietario lo edita) define `Phase` y `Closed` de cada estado. PROJECT KMV los calcula con fórmulas de columna (cada fila depende sólo de su propio `Project Status`). Filtro compartido `Open` (`Closed` sin marcar) aplicado a la Dynamic View KMV - PERMITS en `Settings > General > Restrict view by sheet filter`; el usuario comprobó que una fila cerrada desaparece. `Project Status` vinculado por el usuario al catálogo (`Status`, sin filtro, "Limit to list values only"): 60 opciones, sin separadores; un estado nuevo se agrega como fila del catálogo con su `Phase` y `Closed`, sin tocar PROJECT KMV. Automatizaciones `DV | New Task` (Designer1, Designer2, Permitting Team) activas.
Falta, en orden:
- Aprobación de la clasificación por la jefa del usuario: dudosos `4. Permit Approved` y `6. Permit - MOT Approved` (hoy abiertos) y `7. As-Built Completed` (hoy cerrado).
- Reportes de PEN-42: filtran abiertos con la lista `APP_CLOSED_STATUSES` y no coinciden con la vista (por ejemplo `4. Permit Expired` y `8. Close - Permit Process`); cambiar su filtro a `Closed` sin marcar en el Report Builder.
- Correos en `Contact List`: de 13 opciones de `Permitting Team`, 6 tienen correo activo; las demás no reciben el aviso `New Task`.
- `Phase` vacía para `IN PERMITTING`, `IN PROGRESS`, `COMPLETE`, `CANCELLED` y `NO PERMIT REQUIRED`: decidir si llevan fase.
- Opcional: condición `Closed` sin marcar en las automatizaciones `DV | New Task` (sus condiciones no se ven por API).
- Backend, tras la aprobación: que la carga de diseñadores (SPEC-B12) lea `Closed` del catálogo en vez de `APP_CLOSED_STATUSES`.
- Estados por equipo en el desplegable: PEN-43.

### PEN-28 Activos asociados a personas y contactos

Prioridad: media. Alcance: backend y frontend. Estado: en curso (2026-10-28, solicitado por el usuario).
Situación: el detalle de persona sólo muestra permisos de hojas. Smartsheet también expone reportes, dashboards, workspaces y carpetas; el backend aún no lista ni obtiene sus permisos o relaciones con hojas.
Hecho: definidas SPEC-B13 y SPEC-10. Hacer: extenderlas a todos los activos, crear endpoint de sólo lectura con caché, fixtures sintéticos y pruebas; después la sección de frontend en el detalle de persona. No se debe inferir acceso a un activo desde una hoja sin que la API lo confirme.

### PEN-12 Exportar

Prioridad: baja. Alcance: backend y frontend. Estado: terminada (2026-10-16): `GET /api/export/access.csv`.
Hacer: exportar a CSV la matriz persona por hoja con niveles. El archivo contiene correos reales: se genera bajo demanda y no se guarda en el servidor.

### PEN-29 Mapa de vías, milepost, jurisdicción y parcelas

Prioridad: media. Alcance: backend y frontend. Estado: en curso (2026-10-31): M1 a M4, buscador, imagen HD, vías y parcelas implementadas. PEN-34 verificó búsquedas por zona y cruces; PEN-35 encuadra el trazo completo; PEN-38 ajusta el recorrido a la red LRS; PEN-39 encuentra cruces con nombre recortado; PEN-40 suma el adaptador de St. Johns (M5) y separa lugares censales de ciudades. Pendientes: resto de M5, comparación independiente con OSP usando idénticos vértices, respaldo de parcelas para Palm Beach/Martin y mapa base con clave opcional. ADR-B16 y ADR-B17 aprobadas por el usuario.
Tipo (ADR-B15): (a) ni Smartsheet ni OSP dicen el milepost, de quién es la calle y qué parcela hay en un punto sin dibujar una solicitud en OSP; el mapa sólo consulta y no cambia cómo se pide el permiso.
Situación: verificado con GET reales que los servicios públicos del FDOT y de FDACS reproducen los valores de OSP (SR 953, vía 87281000, sección 281, milepost 3.124 a 3.839) y dan ciudad, condado, ZIP y parcela en Broward, Palm Beach, Martin y Miami-Dade. Investigación en `future_docs/`.
Specs: SPEC-B14 (backend) y SPEC-11 (frontend); ADR-13 del frontend (Leaflet).
Fases:
- M1 backend punto: transporte GIS sin token, cliente, catálogo de capas, reglas puras (milepost, jurisdicción, usos DOR), `GET /api/map/point`, `GET /api/map/sources`, pruebas con `respx` y verificación manual.
- M2 backend tramo: `GET /api/map/segment` con `osp_row` y geometría.
- M3 frontend punto: destino "Mapa" en la navegación, `/mapa`, mapa base USGS, clic o coordenadas, panel con vía, jurisdicción, ubicación, parcela y fuentes.
- M4 frontend tramo: dos clics, tramo resaltado y "Copiar para OSP".
- M5 adaptadores de condado: St. Johns (`MAINTENANCE`, PEN-40); Palm Beach (`RESP_AUTH`); Broward, Martin y Miami-Dade según MJ-PEN-01 a MJ-PEN-03.
- M6 extras: capas de vías dibujadas, búsqueda por dirección (hecha: buscador del mapa, SPEC-B14 punto 9), Turnpike (GIS-PEN-01) y mapa base de Esri con clave.
Límites: la jurisdicción de calles locales es aproximada hasta M5; USGS sólo tiene teselas hasta el zoom 16 en Miami (verificado), por lo que el detalle de calle se ve ampliado y algo borroso hasta M6.

### PEN-30 Mapa: una fuente caída no frena la respuesta, y parcela de respaldo

Prioridad: alta. Alcance: backend y frontend. Estado: terminada para Broward (2026-10-30): primer punto 6,0 s y siguientes 1,6 s con FDACS caído, folio del condado y su fuente en el panel (SPEC-B14 CA-14 y CA-15, SPEC-11 CA-12).
Tipo (ADR-B15): (b) el mapa ya existe; esto lo hace usable cuando una fuente pública falla.
Situación: el 2026-10-30, desde el equipo Windows, `gis.fdacs.gov` no aceptó conexiones (DNS sí, TCP no; FDOT respondía en menos de 1 s). Cada punto tardaba 60,5 s (tres intentos de 20 s) y llegaba sin parcela; el panel parecía colgado en "Consultando FDOT y FDACS…" y en "Calculando el tramo…".
Hacer: plazo de conexión corto (`gis_connect_timeout_seconds`, 5 s) y sin reintentos cuando ni siquiera conecta; si FDACS falla en Broward, pedir la parcela a la capa pública del condado (`services.arcgis.com/JMAJrTsHNLrSsWf5/.../Parcels/FeatureServer/0`, `FOLIO`; MJ-BR-01, verificada desde este equipo el 2026-10-30) y decir de qué fuente salió. Specs: SPEC-B14 y SPEC-11.
Pendiente aparte: respaldo de consulta de parcela para Palm Beach, Martin y Miami-Dade (MJ-PEN-02 a MJ-PEN-04); revisar las condiciones de uso de la capa de Broward (MJ-PEN-06). PEN-37 implementa Actualizar con `refresh=true` en punto y trazo; los contornos de Miami-Dade ya usan la fuente del condado (PEN-33).

### PEN-31 Mapa: mejor vista y más zoom

Prioridad: media. Alcance: frontend. Estado: terminada (2026-10-30): "Satélite HD (NAIP, más zoom)" hasta zoom 20, "Vías del FDOT" con leyenda, escala en metros y pies, Estado en Ubicación; preferencias guardadas en el navegador (SPEC-11 CA-13). La NAIP tarda unos 8 s en llenar la vista a zoom 19: queda como opción, no por defecto.
Tipo (ADR-B15): (b) mejora del mapa propio, a pedido del usuario: "estar un poquito más cerca y con mejor vista", como opciones si pesan.
Situación: verificado el 2026-10-30: USGS NAIP Plus (`imagery.nationalmap.gov/.../USGSNAIPPlus/ImageServer`, dominio público, sin clave, píxel de 30 cm) entrega a zoom 18 detalle de autos y carriles en Fort Lauderdale, contra la tesela de USGS que se queda en zoom 16; la exportación del FDOT (`RCI_Layers/MapServer/export`, con `dynamicLayers`) dibuja vías estatales y de condado con colores propios en 0,7 s.
Hacer: mapa base "Satélite HD (NAIP)" hasta zoom 20, capa opcional "Vías FDOT", escala en pies y metros y el estado (Florida) en Ubicación. Spec: SPEC-11; ADR-13 amplía su excepción de teselas a estos dos servicios.

### PEN-32 Trazo como en OSP y tabla Work Location

Prioridad: alta. Alcance: backend y frontend. Estado: terminada (2026-10-30): modo "Trazo" en lugar de "Tramo", `GET /api/map/trace`, tabla Work Location copiable; con GET reales el caso de control da la fila de OSP (Miami-Dade, SR 953, 281, 3.124 a 3.839, No) y un giro de SR 953 a SR 968 da dos filas que se juntan en el cruce (SPEC-B14 CA-16 a CA-18, SPEC-11 CA-14). Pendiente: comparar el Turnpike con OSP en un tramo del Turnpike.
Tipo (ADR-B15): (a) OSP sólo da la tabla tras dibujar dentro de una solicitud; aquí se obtiene sin abrir una.
Situación: pedido del usuario: "para el milepost se debe hacer siempre un trazo". En OSP (paso 3, `future_docs/osp-milepost-paso3.png`) se marca un punto, se dibuja la línea por el recorrido, se termina con doble clic y sale la tabla Work Location: County, State Road ID ("SR 953", no el ID de vía 87281000 que mostraba el panel), Section Number, Beginning y Ending Milepost e "Is Location on Turnpike?". El modo Tramo sólo aceptaba dos puntos sobre una misma vía.
Verificado el 2026-10-30: la capa 8 del FDOT acepta consultas por rectángulo y devuelve las vías candidatas; la capa 13 de `Admin_Boundaries` ("District Bndy w TPIKE") da el polígono `D8`/`FTE` sobre SR 821 (Turnpike) y sólo `D6` sobre SR 953 (resuelve GIS-PEN-01).
Hacer: `GET /api/map/trace` con la línea dibujada; una fila por cada vía que sigue el trazo (sin contar los cruces), con mileposts, condado, State Road ID como ruta ("SR 953"), sección y Turnpike; modo "Trazo" en el mapa con clic por vértice, doble clic o "Terminar", "Deshacer" y tabla copiable. Specs: SPEC-B14 y SPEC-11.

### PEN-34 Ubicarse por condado, ciudad, calle y cruce

Prioridad: alta. Alcance: backend y frontend. Estado: terminada (2026-10-31, pedida por el usuario para probar en Fort Lauderdale, Broward): SPEC-B14 puntos 9, 12 y 13 (CA-20 a CA-22) y SPEC-11 (CA-16 y CA-17).
Tipo (ADR-B15): (a) ni OSP ni Smartsheet llevan a un cruce de calles con su milepost; el mapa sólo consulta.
Hecho: selectores Condado (los cuatro donde trabaja el equipo primero) y Ciudad (sólo municipios del condado) que encuadran el mapa y dibujan el límite; el buscador se acota a la zona, suma calles locales del Censo (TIGER) y entiende cruces "A & B" o el campo "Cruce con": el FDOT da el milepost del cruce, el Censo cubre calles locales y, si no se cruzan, el punto más cercano con su distancia.
Límite: el firewall de census.gov bloquea la IP tras ráfagas de consultas (B-15); mientras dure, las calles locales y las direcciones no responden y queda lo del FDOT (vías estatales y de su inventario).

### PEN-35 Trazo ajustado a la geometría oficial del FDOT

Prioridad: alta. Alcance: backend y frontend. Estado: terminada (2026-10-31).
Situación: el trazo ya clasifica cada muestra contra la LRS del FDOT y las filas llevan una geometría oficial recortada, pero el mapa conserva encima la polilínea manual y reporta su longitud. Eso hace parecer que el resultado no se acomoda a la vía, aunque los mileposts sí se calculan sobre ella.
Hacer: tras terminar, mostrar sólo las geometrías LRS de las filas como resultado; reservar la línea punteada para la edición. `length_mi` será la longitud de esas geometrías oficiales e `input_length_mi` conservará la longitud dibujada para explicar diferencias. Al cargar un enlace de trazo, encuadrar todas las geometrías devueltas. Probar la regla pura, contrato, componente y E2E. No se hace enrutamiento: un trazo que pase por otra vía o quede a más de 25 m sigue requiriendo que la persona lo corrija.

### PEN-36 Evidencia del ajuste de extremos del trazo

Prioridad: alta. Alcance: backend y frontend. Estado: terminada (2026-10-31).
Situación: el resultado ya dibuja la LRS oficial, pero la persona no puede comprobar en cifras cuánto se movieron los extremos elegidos hasta esa vía. Esto hacía parecer que el panel conservaba la línea manual.
Hacer: `GET /api/map/trace` devuelve la distancia en metros desde el primer y último punto marcados a sus vías LRS elegidas. El panel la explica como ajuste de FDOT junto a la longitud oficial. Cero metros significa que el punto ya estaba sobre la geometría; no implica que se haya hecho enrutamiento.

### PEN-37 Integridad del trazo y geometrías LRS fragmentadas

Prioridad: alta. Alcance: backend y frontend. Estado: terminada (2026-10-31); comparación independiente con OSP sigue en PEN-29 y OSP-PEN-01.
Evidencia: una LRS sintética partida en MP 0–0.5 y 0.5–1 devolvía sólo 0.2–0.5 al pedir 0.2–0.8; un dibujo que sale más de 25 m de la calle y vuelve se unía sin informar el hueco.
Hacer: unir segmentos LRS contiguos por medida y posición, incluso invertidos o repetidos; sin puente artificial entre fragmentos desconectados. Separar filas ante huecos del dibujo; devolver cobertura estimada por muestras de 10 m (`matched_percent`, `unmatched_length_mi`) y `TRACE_PARTIAL` si falta recorrido, `TRACE_GEOMETRY_INCOMPLETE` si la geometría de una fila está incompleta. Longitud desconocida en `null`, nunca cero supuesto. Explicar estas situaciones en el panel y conservar el dibujo cuando el resultado está incompleto. Distancias calculadas en plano local con corrección de longitud por latitud.
Incluye cerrar el botón Actualizar de PEN-30 para punto y trazo: salto real de caché del backend con `refresh=true`, errores visibles y consultas deshabilitadas sin selección.
Límite de evidencia: las coordenadas del caso SR 953 se obtuvieron a partir de los MPs de la captura; eso verifica la interpolación, no demuestra equivalencia independiente con el algoritmo de OSP para cualquier dibujo. Sigue pendiente comparar entradas idénticas en ambos sistemas (OSP-PEN-01).

### PEN-38 Ajuste automático del recorrido dibujado

Prioridad: alta. Alcance: backend y frontend. Estado: terminada (2026-10-31, solicitado por el usuario).
Evidencia real (GIS del FDOT, 2026-10-31): el control de OSP sigue en SR 953 MP 3.124–3.839; corrido 50 m al oeste vuelve a SR 953 (3.125–3.839) cuando el modo estricto daba una vía local; una diagonal de LeJeune a W Flagler pasa de 0.893 a 1.221 mi en dos filas (SR 953 3.118–3.839 y SR 968 4.534–5.032); Broward Blvd dibujado 45 m al norte vuelve a SR 842 (6.775–7.166). Revisión visual a 1440 y 320 px sin desborde.
Situación: PEN-35 a PEN-37 recortaban la geometría de las vías detectadas, pero no reconstruían un recorrido entre vértices fuera del eje o separados por curvas. El usuario necesita que la línea se desplace, se alargue/acorte y se divida en más tramos cuando cambia de vía.
Hacer: ajuste geométrico sobre un grafo local de segmentos LRS, con proyección de vértices, continuidad espacial, búsqueda de recorrido y una fila por vía recorrida; tolerancia visible de 100 m en el frontend. Comparación con el original y modo estricto anterior disponibles. URL y claves de caché incluyen la opción. Sin camino, fuera de tolerancia o grafo demasiado grande: resultado estricto de respaldo con aviso; rutas alternativas similares y conexiones geométricas entre vías se identifican para revisión.
Límites: no hay datos de giros ni elevación/topología de OSP en esta capa; una conexión en planta puede ser un paso a desnivel y se informa. Esta mejora no se presenta como reproducción exacta del algoritmo privado de OSP.

### PEN-39 Cruces del FDOT con el nombre recortado

Prioridad: media. Alcance: backend. Estado: terminada (2026-10-31); SPEC-B14 CA-29.
Evidencia: en Fort Lauderdale "Sunrise Blvd & Federal" encuentra el cruce, pero "Federal Hwy & Sunrise" no devuelve nada. La capa 6 de RCI recorta `INTSEC_ROA` a 20 caracteres ("US-1/SR-5/FEDERAL HW", "US-1/SR-5/N FEDERAL"), así que "FEDERAL HWY" no coincide.
Hacer: si el nombre completo no da el cruce, reintentar una vez sin el tipo de vía final (HWY, BLVD, AVE…), en la calle que cruza y en la vía (la capa 13 también recorta: "US-1/SR-5/FEDERAL", vía 86020000), sólo si queda una palabra de 3 letras o más ("SE 3 AVE" no se recorta). Prueba pura del filtro y prueba con GIS simulado.
Fuera de alcance: cruces que no existen a nivel (Federal Hwy pasa en túnel bajo Las Olas); esos dependen del punto más cercano de TIGER (B-15).

### PEN-40 Mapa: de quién es la calle en St. Johns y zonas no incorporadas con nombre

Prioridad: alta. Alcance: backend y frontend. Estado: terminada (2026-11-03); SPEC-B14 punto 5 y CA-30 a CA-32, SPEC-11 CA-21. Pendiente aparte: condiciones de uso del servicio del condado (MJ-PEN-06).
Tipo (ADR-B15): (b) el mapa ya dice de quién es la calle; esto cambia la aproximación por el dato oficial del condado, sin escribir nada.
Situación: pedido del usuario: en St. Johns County la respuesta es limitada. GET reales del 2026-11-03 con el servicio del panel: FDOT y FDACS responden (condado 78, Distrito 2, parcela DOR 65), pero las calles locales no están en la LRS del FDOT ("No hay vía cercana" en World Golf Village y St. Augustine Beach), y Nocatee y World Golf Village salen como ciudad (`CITY`, `inside_city`) aunque son lugares censales (CDP, `CLASSFP` U2), es decir, zona no incorporada del condado. El error de la ciudad afecta a todos los condados.
Hacer:
- adaptador de condado M5 para St. Johns: capa pública `https://www.gis.sjcfl.us/sjcgis/rest/services/Road/MapServer/36` con el campo `MAINTENANCE` (quién mantiene cada tramo; MJ-SJ-01 a MJ-SJ-04), sólo si el FDOT dice condado 78;
- la ciudad del punto sólo si la capa 7 de `Admin_Boundaries` dice municipio (`CLASSFP` C1); un lugar censal pasa a `location.place` y la jurisdicción cae en `unincorporated`;
- frontend: mostrar el lugar censal y la nueva fuente.
Fuera de alcance: parcelas del condado (FDACS responde en St. Johns y su `PARCEL_ID` es el `STRAP` del condado) y el trazo de OSP, que sólo usa vías del FDOT.

### PEN-41 Mapa: calles coloreadas por jurisdicción y qué permiso pedir (St. Johns)

Prioridad: alta. Alcance: backend y frontend. Estado: terminada (2026-11-03); SPEC-B14 punto 5, puntos 14 y 15 y CA-33 a CA-37, SPEC-11 puntos 11 y 12 y CA-22 a CA-24.
Tipo (ADR-B15): (a) ni el iMAP del condado ni el tasador colorean las calles por quién las mantiene ni dicen qué permiso pedir en un recorrido; el panel sólo consulta y no cambia cómo se pide el permiso.
Situación: pedido del usuario con capturas de Google Earth (trazo rojo por CR 210 W hacia Harbor Chase of Beach Walk) y del iMAP del condado. GET reales del 2026-11-03: en esa zona la LRS del FDOT no tiene vías a 1,5 km y su capa de vías de condado ubica CR 210 (`78510000`) a más de 30 m del eje; el condado sí tiene CR 210 W (`St Johns County`) y Beachwalk Blvd. Una celda de 0,02 grados trae de 99 a 409 tramos en 1,2 a 2,8 s, sin pasar el límite de 1000.
Hacer:
- `GET /api/map/streets` por celda: tramos del condado con quién los mantiene, sólo donde hay adaptador (St. Johns);
- `GET /api/map/trace/streets`: calles del condado que sigue un trazo, con su responsable y longitud;
- separar la jurisdicción en Estado (FDOT), condado, city, town y village (pedido del usuario; `LSAD` del Censo: 25, 43 y 47);
- frontend: casilla "Jurisdicción de calles" que colorea las calles por responsable con leyenda y nombre al pasar el cursor; en el punto y en el trazo, qué permiso corresponde según el responsable (OSP para el FDOT, derecho de vía del condado o de la ciudad, autorización del dueño o del CDD), como guía que hay que confirmar.
Fuera de alcance: pedir o tramitar permisos, y otros condados (siguen sin fuente propia).

### PEN-33 Límites de parcelas en el mapa

Prioridad: media. Alcance: backend y frontend. Estado: terminada para Broward y Miami-Dade (2026-10-30): casilla "Límites de parcelas" a zoom 17 o más, `GET /api/map/parcels` por celda (SPEC-B14 CA-19, SPEC-11 CA-15). El resto del estado depende de FDACS.
Tipo (ADR-B15): (b) lo que muestran los mapas del tasador, dentro del mismo mapa del panel.
Situación: pedido del usuario: ver "cómo se separan" los lotes y las calles, como en un GIS o el mapa del tasador. Verificado el 2026-10-30 desde el equipo Windows: Broward (`services.arcgis.com/JMAJrTsHNLrSsWf5/.../Parcels/FeatureServer/0`, 37 parcelas en 0,8 s) y Miami-Dade (`gisweb.miamidade.gov/.../MD_LandInformation/MapServer/26`, 173 parcelas en 0,6 s) devuelven polígonos por rectángulo en GeoJSON; simplificados a ~0,5 m pesan unos 30 a 50 KB. FDACS (todo el estado) no responde desde este equipo (B-13).
Hacer: `GET /api/map/parcels` por celda pequeña, sólo con el ID de parcela (sin propietarios), Broward y Miami-Dade por condado y FDACS para el resto; casilla "Límites de parcelas" que dibuja las líneas a zoom 17 o más.
Pendiente aparte: Palm Beach (`maps.co.palm-beach.fl.us/.../Parcels/Parcels/MapServer`) y Martin; Miami-Dade también publica "County Maintained Road" (capa 8 de `MD_LandInformation`), útil para M5.

### PEN-42 Reportes de Smartsheet sobre Presentable

Prioridad: media. Alcance: Smartsheet (configuración, sin código). Estado: hecho (2026-11-10 12:47 -05:00).
Pedido: reportes en `Pruebas/Producto` con Presentable como origen, a partir de los reportes "Diego Miranda 2026", "Carlos Carrillo XXVI" y "All Records Request" y de la hoja `Invoices (Piloto)`.
Hecho: creados con el conector de Smartsheet (`create_report`): `Presentable | Permitting por persona` (columnas del de Diego, todo el equipo agrupado por Permitting Team, sólo proyectos abiertos según `APP_CLOSED_STATUSES`), `Presentable | MOT y Paquetes (Carlos / German)` (Permitting Team Carlos Carrillo o Designer1/Designer2 Carlos Carrillo o German Quiñe, abiertos), `Presentable | Invoices` (filas con PM Approval Date o alguna fecha de factura, agrupado por Invoice Status y Customer) y `Presentable | All Records Request` (Primary = KMV-P, como el original). Se agregó a Presentable la columna fórmula `Invoice Status` (misma lógica que `Invoices (Piloto)`).
Avance 2026-11-11 09:50 -05:00: columna `Email Permitting` (CONTACT_LIST, fórmula contra el Directorio de `Contact List`, igual que `Correo Designer1`) agregada después de `Permitting Team` en PROJECT KMV. De los 12 nombres de Permitting Team, 5 tienen correo activo en el Directorio; faltan 2 personas, 3 sin correo y 2 inactivas. La automatización de aviso no se puede crear por API (`POST automationrules` no existe); se crea en la interfaz.
Límites: los filtros de los reportes originales no son visibles por API y se dedujeron de sus datos; se ajustan en el Report Builder o con `update_report_definition`. Smartsheet no tiene filtro de persona elegible por quien mira: se agrupa por persona.

### PEN-43 Estados por equipo en el desplegable

Prioridad: media. Alcance: Smartsheet (PROJECT KMV y Project Status Catalog). Estado: propuesta (2026-11-11 16:45 -05:00); espera que el usuario confirme el reparto de estados y la regla de precedencia.
Pedido: que Designer1, por un lado, y Permitting Team y Designer2 (mismo equipo), por otro, sólo vean y elijan en el desplegable los estados que les tocan.
Límite nativo: el filtro de un desplegable vinculado es uno por columna y vale para todos; Dynamic View y formularios usan la lista de la columna (SPEC-B16 LD-03, LD-07). No hay listas por persona ni por vista.
Diseño propuesto:
- Catálogo: casillas `Design` y `Permitting` por estado; un estado puede tener las dos.
- PROJECT KMV: desplegables `Design Status` (vinculado a `Status`, filtro `Design` marcada) y `Permit Status` (filtro `Permitting` marcada), ambos con "Limit to list values only".
- `Project Status` pasa a fórmula: `=IF(NOT(ISBLANK([Permit Status]@row)), [Permit Status]@row, [Design Status]@row)`. `Phase`, `Closed`, la vista, los reportes y las automatizaciones siguen leyéndolo; deja de editarse a mano y reemplaza su vínculo actual con el catálogo.
- Cada Dynamic View edita sólo la columna de su equipo y muestra `Project Status` de sólo lectura.
Reparto propuesto por el nombre de los estados, sin confirmar: Design = fases 1, 2, 5 y 7; Permitting = fases 3, 4, 6, 8 y 9, `IN PERMITTING` y `NO PERMIT REQUIRED`; ambos = `IN PROGRESS`, `COMPLETE` y `CANCELLED`.
Costo: si el proyecto vuelve a diseño después de permisos, `Project Status` muestra el estado de permisos. Que gane el último cambio sólo es posible con el servicio propio y depende del backend encendido.
Trabajo por API (sólo Pruebas, con autorización expresa): casillas del catálogo, columnas nuevas, traslado de los estados actuales de las filas y fórmula de `Project Status`, comprobando `Phase` y `Closed`. En la interfaz, el usuario: vincular las dos columnas con su filtro, ajustar cada Dynamic View y revisar automatizaciones que se disparen por cambios de `Project Status`.

### PEN-44 Hoja hija sincronizada con PROJECT KMV (consulta)

Prioridad: media. Alcance: Smartsheet. Estado: en curso (2026-11-12). La hoja hija sincronizada se descartó; el usuario eligió separar por cliente con la Dynamic View restringida por `Client Access`, el reporte KMV - Customers para el Excel y el aviso `Client | Status Update` (detalle abajo y en `HOJA_PROJECT_KMV.md` HK-21 y HK-32 a HK-34). Falta configurar y probar la vista con una cuenta que no sea la dueña y el primer envío real del aviso.
Pedido: una hoja derivada de la general que reciba sus cambios y también los devuelva.
Nativo (verificado 2026-11-11 en la ayuda y la comunidad de Smartsheet): no hay sincronización bidireccional entre hojas. Ida y vuelta sólo con Dynamic View y reportes, que no son hojas (sin columnas ni fórmulas propias). Hacia la hija, un solo sentido: cell linking (celda por celda, celdas destino no editables, filas nuevas no llegan solas), fórmulas entre hojas, "Copy rows" (copia única) y DataTable (plan Advance). Bidireccional: Bridge (complemento de pago) o herramientas externas.
Con el servicio propio: posible, porque ya vigila la hoja y escribe, pero exige una llave única por fila (el Tracking ID se repite en las hijas), resolver conflictos, evitar bucles, elegir columnas (las de fórmula no se copian), evitar avisos duplicados de automatizaciones y aceptar 5 a 15 s de demora; además duplica la fuente de verdad (ADR-B15).
Recomendación: Dynamic View si basta con ver y editar filas y columnas; hoja sincronizada sólo si el equipo necesita columnas, automatizaciones o permisos propios.
Uso indicado por el usuario (2026-11-12): una hoja con sólo las columnas del reporte de seguimiento de cliente `Tracker 2026 - KMV` (14 columnas: Tracking Project, Project Name, Project Address, City, County, Contractor, Date Received, Submitted Date, Permit Approved, Permit Expires, Project Status, Agency, Permit # y Obs; filas de permisos), con filtros propios y Dynamic Views por cliente o compañía. Recomendación: Dynamic View directa sobre la maestra del año, con esas columnas y un filtro compartido por cliente (o restricción por una columna de contacto del cliente); sin hoja intermedia ni sincronización. Exportar a Excel (motivo del usuario para la hoja hija): Dynamic View no exporta a Excel; un reporte con esas 14 columnas y el filtro del cliente sí (exportación manual o envío programado como adjunto Excel por correo), y puede tomar varias maestras anuales. Exportar la hoja exporta todas sus columnas, así que la hoja hija no aporta para esto.
Guía de filtro por cliente (2026-11-12, sin cambios hechos por el servicio): `Customer` es una columna desplegable de PROJECT KMV (11 opciones) y la hoja tiene un solo filtro compartido (`Open`). Uso interno: agregar `Customer` a las columnas de la Dynamic View para filtrar con su botón Filter. Para clientes: una Dynamic View por cliente, cada una limitada con un filtro compartido de la hoja que combine `Customer` y `Closed` (la vista acepta un solo filtro), así la vista y su descarga CSV sólo traen las filas de ese cliente.
Opción dinámica (verificada 2026-11-12 en la ayuda y la comunidad de Smartsheet; recomendada, sin decisión): los filtros de hoja tienen valores fijos y no leen catálogos, pero la Dynamic View puede restringir las filas al usuario que la abre mediante una sola columna de contactos, combinada con un filtro compartido (`Open`). Propuesta: columna de contactos múltiples en `Customer List` con las personas de cada cliente y otra en PROJECT KMV con fórmula de columna `INDEX`/`MATCH` por `Customer` (fórmulas que devuelven contactos funcionan si la columna de origen también es de contactos; probar con varios contactos). Una sola vista para todos los clientes; un cliente nuevo sólo requiere su fila en `Customer List`. Requiere que cada persona entre con una cuenta de Smartsheet con ese correo.
Reportes y acceso (verificado 2026-11-12, comunidad y ayuda de Smartsheet): compartir un reporte no basta, quien lo ve necesita acceso a las hojas de origen; el usuario no quiere dar acceso a la carpeta. Sin dar acceso: la Dynamic View (comparte sólo la vista) y el envío programado del reporte como adjunto Excel a correos escritos a mano (sin cuenta ni acceso). Publicar el reporte crea un enlace de sólo lectura que cualquiera con el enlace puede abrir: no se recomienda para datos de clientes.
Decisión del usuario (2026-11-12): Dynamic View con restricción por contactos (faltan la columna de contactos en `Customer List` y en PROJECT KMV, y la configuración de la vista) y, para quien no use la vista, un reporte por `Customer Code` con envío programado del Excel. Un reporte no cambia de contenido según el destinatario (el envío se genera como quien lo programa): para envíos a pedido basta un solo reporte: cambiar el código en Report Builder, guardar, revisar las filas y enviar el Excel a mano (sólo programa automático por cliente exige un reporte propio, armado con Save as New cambiando sólo el código); las filas nuevas entran solas. Ese reporte de envíos no se comparte con el equipo, porque muestra el último cliente elegido.
Hecho (2026-11-12, autorizado por el usuario, API en Pruebas): columna `Client Contacts` (contactos múltiples, índice 2) en `Customer List`; referencias `Customer List Customer` y `Customer List Client Contacts` en PROJECT KMV; columna `Client Access` (contactos múltiples, índice 21, junto a `Customer`) con fórmula de columna `=IFERROR(INDEX({Customer List Client Contacts}, MATCH(Customer@row, {Customer List Customer}, 0)), "")`. Todo en inglés por pedido del usuario. No se probó con correos ficticios: PROJECT KMV tiene 3 avisos activos (`DV | New Task ...`) cuyo disparador la API no muestra, y un cambio de fila podría enviar avisos al equipo. Falta: que el usuario cargue los correos reales de un cliente, verificar por API que `Client Access` los recibe (también con varios), configurar en la vista para clientes el filtro `Open` y la restricción por `Client Access` (sin `Open`, ver decisión), y probar con una cuenta que no sea la del dueño.
Reporte de envíos `KMV - Customers` (creado por el usuario, leído por API 2026-11-12): 14 columnas del tracker de cliente, pero con dos fuentes, PROJECT KMV y `Customer List` (20 filas: 9 + 11 del catálogo). Recomendado: dejar sólo PROJECT KMV como fuente; el cliente se elige en Filter Criteria con `Customer` is one of y se cambia en cada envío.
Avance (2026-11-12 16:41, lectura por API): el usuario cargó 2 contactos de prueba en `Client Contacts` para `BS-Blue Stream` y `CC-Crown Castle`; las 9 filas de PROJECT KMV tienen en `Client Access` exactamente los contactos de su cliente (la fórmula `INDEX` copia varios contactos). El reporte quedó sólo con PROJECT KMV como fuente. Falta: configurar la restricción por `Client Access` en la Dynamic View de clientes (la API pública no lee Dynamic Views), probar con una cuenta que no sea la del dueño y confirmar si llegaron avisos `New Task` al cargar los contactos.
Decisión del usuario (2026-11-12 16:45): la vista de clientes va sin el filtro `Open` (`Closed` is not checked); el cliente ve todo lo del año, también lo cerrado, y sólo se restringe por `Client Access`. Puede revisarse más adelante.
Aviso al cliente (2026-11-12 16:53, pedido y autorizado por el usuario, conector de Smartsheet): automatización `Client | Status Update` (id 1825411349931908) en PROJECT KMV, activa: cuando una fila existente cambia `Project Status` a uno de 21 estados (los 19 del reporte `Tracker 2026 - KMV` que existen en el desplegable, más `IN PERMITTING` y `COMPLETE`) y `Client Access` no está vacío, envía un correo en inglés a esos contactos con asunto `Project Update – {Tracking Project}: {Project Status}`, mensaje cordial, enlace a la Dynamic View de clientes y 10 columnas (sin adjuntos ni comentarios). Falta: prueba real cambiando el estado de una fila con contactos de prueba. Un cambio simultáneo en madre e hija envía dos correos.
Corrección: `DV | New Task Permitting Team` se disparaba con `Designer1` y comprobaba `Email Designer1`; ahora vigila `Permitting Team` y comprueba `Email Permitting` (mismo patrón que Designer1 y Designer2). Las otras automatizaciones sólo se disparan con sus columnas: cargar contactos no envía avisos.
Ajuste (2026-11-12 17:25, pedido del usuario): `DV | New Task Designer1` lleva en asunto y mensaje `Tracking Project` y `Project Name` de la fila; `DV | New Task Designer2`, además `Agency`. Disparadores, destinatarios, columnas y enlaces sin cambios.
Comparación con Bridge: el servicio cumple el papel reactivo de Bridge y añade registro transaccional (IDs sin repetirse, auditoría, recuperación) y pruebas automáticas; Bridge corre en la nube de Smartsheet, reacciona por eventos y no necesita servidor. Para producción el backend debe ir a un servidor siempre encendido (B-16).

### PEN-45 Capacidad de la hoja maestra y una maestra por año

Prioridad: alta. Alcance: Smartsheet y ID Manager. Estado: decidido por el usuario (2026-11-12 12:14 -05:00): una hoja maestra por año con todos los clientes; falta planificar e implementar. Revisión (2026-11-12 19:10): medido con los originales, un año completo (unas 4 074 filas de Crown Castle y Blue Stream en 2026) no entra con 140 columnas; hay que quitar columnas (análisis abajo, falta la decisión del usuario) o revisar la decisión.
Situación: el límite de una hoja es 500 000 celdas contando filas por columnas, vacías incluidas, con un máximo de 20 000 filas y 400 columnas (ayuda oficial de Smartsheet). PROJECT KMV tiene 140 columnas desde el 2026-11-12 (139 antes de `Client Access`): caben unas 3 571 filas. Con la estimación del usuario de unas 3 000 filas por año, todos los clientes, un año ocupa unas 420 000 celdas (84 %), así que no caben varios años en una hoja. Vista de tabla verificada en la ayuda oficial (2026-11-12 18:59, artículos 2483460, 2483463 y 2483893): como vista es igual a grid en datos y límites (500 000 celdas), está en todos los planes, permite volver a grid y mantiene jerarquía, fórmulas, formato condicional, Dynamic View, automatizaciones, formularios y conversaciones; no tiene publicar, reemplazar, recordatorios de fila, correo a compartidos, MS Project ni Work Insights; agrega desplegables vinculados con filtrado estático y dinámico (probar para PEN-43 y SPEC-B16 LD-09) y column linking. El millón de celdas (100 000 filas) es sólo para hojas a gran escala, sólo con plan Enterprise y sólo en vista de tabla; la vista grid queda desactivada y no se admiten automatizaciones, app móvil, Bridge, DataMesh, DataTable, conectores ni los endpoints Get column, Get columns, Get row, Copy rows, Move rows, Send rows y Copy sheet, que el servicio usa. Conclusión: no pasar la maestra a gran escala; quedarse bajo 500 000 celdas. El usuario mencionó lentitud en equipos antiguos; la ayuda no lo trata. La cuenta es Enterprise (confirmado por el usuario, 2026-11-12 19:00). Impacto en el servicio si la hoja pasara a gran escala: fallarían `list_columns` (Get columns) y `get_row` (Get row), que usan IDs, Obs, catálogo y la escritura del Stable ID (unas 20 llamadas en `ids/gateway.py`, `ids/pilot.py`, `obs/sync.py`, `sheets.py` y el propio cliente). Es adaptable sin tocar a los llamadores: reimplementar esos dos métodos del cliente con Get sheet (columnas de la hoja y filtro `rowIds`), que no figura como no admitido. El bloqueo real son las automatizaciones (`Client | Status Update`, `New Task`, `LT Records`) y la app móvil, que la ayuda marca como "aún no admitidas". Plan B, sin decisión.
Opciones:
- Una maestra por año con todos los clientes: coincide con el año del ID, pero queda justa (84 %) y cada año hay que rehacer Dynamic Views, automatizaciones, referencias entre hojas, desplegables vinculados y formatos; los proyectos abiertos que cruzan de año obligan a trabajar en dos hojas.
- Recomendada: una hoja activa con los proyectos abiertos de todos los años y un archivo por año con los cerrados. La activa queda pequeña y rápida, y las vistas y automatizaciones se configuran una sola vez.
Riesgos de la recomendada: la automatización nativa "Move rows" pierde la jerarquía en la hoja destino (comunidad de Smartsheet); los IDs se conservan porque el servicio escribe el Stable ID también en las hijas. Hay que definir cuándo se archiva un proyecto (madre e hijas cerradas), qué pasa al reabrir (fase 9) y adaptar el ID Manager para que reconozca filas archivadas y la fórmula provisional no proponga números ya usados en el archivo.
Métricas: los dashboards toman datos de reportes que combinan varias hojas (hasta 50 000 filas por reporte; los agrupados se ven por páginas de 2 500) y de hojas de métricas con fórmulas entre hojas. Las columnas de días con `TODAY()` siguen contando en proyectos cerrados sin fecha final y distorsionan los promedios.
Decisión (2026-11-12): una maestra por año con todos los clientes, aunque la recomendación era hoja activa más archivo. Catálogos (Project List, Customer List, Project Status Catalog, Contact List) compartidos entre años.
Hacer:
- Regla de ubicación: cada proyecto va a la hoja del año de su `Date Received`; un proyecto abierto que cruza de año sigue en su hoja.
- Creación anual con "Save as New" sin datos: los desplegables vinculados se conservan apuntando al mismo catálogo (ayuda oficial); las referencias entre hojas pueden romperse (comunidad) y se recrean por API; Dynamic Views nuevas en la interfaz; reportes con origen en un workspace propio de las maestras (las hojas nuevas entran solas) o agregando la hoja a mano.
- ID Manager: lista de maestras por año en vez de una sola hoja; vigilar cada 5 s sólo el año en curso y el anterior mientras tenga abiertos; `Project List` alimentado desde todas las maestras.
- `Control Linked Tracking`: validar contra `Project List` con referencias entre hojas, para que un vínculo a un proyecto de otro año no quede como `LEGACY: NOT LOADED`.
- Capacidad: unas 420 000 celdas por año (84 %) con 3 000 filas y 140 columnas; quitar columnas sin uso para ganar margen.

Análisis de columnas (2026-11-12 18:51; superado por `ANALISIS_COLUMNAS_KMV.md`, verificado el 2026-11-13 09:10: sólo medía Crown Castle y Blue Stream y no detectó los reportes `Permitting` y `MOT y Paquetes`, cuyo alcance es PROJECT KMV pero sin filas la API no lista su hoja de origen; sus cifras y grupos ya no rigen): los originales `8. Crown Castle Fiber - Engineering Plan 2026` y `8. Blue Stream - Engineering Plan 2026` tienen 117 columnas cada uno; PROJECT KMV tiene 140 (las 117 menos `Record ID`, que en KMV es `PRR #`, más 24 nuevas). Filas por año (CC + BS): 2024 2 249, 2025 3 656 y 2026 3 527 al 12-nov (proyección 4 074). Con 140 columnas caben 3 571 filas: un año completo ya no entra; la estimación de 3 000 filas quedó corta.
- Sin uso real (≤0,2 % en 2024 a 2026) y sin dependencias: `CAD Update`, `CADDING`, `Bond?`, `Bond Fee Application`, `Runner Pick up`, `Inspection Date`, `Inspection Pass`, `Invoice GALP # Days` y `PM Approval Invoices Days` (vacías y sin fórmula); más `Project Number` y `Frozen Number`, que dejaron de usarse con ID-48 e ID-49 (quitarlas impide volver a la fórmula provisional). 11 columnas: quedarían 129 (3 875 filas).
- Uso mínimo (≤2 %, pocas filas al año): `Aerial` (columna del reporte Invoices), `Tone Locating`, `Runner Submitting`, `Survey Certified`, `Additional Site Survey`, `Sonde FTG`, `GPR`, `Permit Coordinator Approved Date (QC)` y el grupo `Sonde Request`, `Sonde Received` y `Sonde # Days`. 11 más: 118 (4 237 filas).
- Nuevas en KMV sin dependencias detectadas, por confirmar con el usuario: `Security Key`, `Future Project #`, `Reminder Sent`, `Mile Post`, `DT Owner` y `Designers List`. 6 más: 112 (4 464 filas).
- Se conservan: `Phase`, `Closed` y `Control Linked Tracking` (filtro `Open`, vistas y formato condicional, que la API no muestra), los grupos de segunda revisión (1,5 a 6,8 %) y as-built (5 a 13 %) y todo lo que usan fórmulas, automatizaciones, reportes o el backend.
- Siguiente palanca si no alcanza: las 18 columnas de días por fórmula (`... # Days`, `Days in ...`).
- Antes de borrar: el usuario revisa que ninguna Dynamic View ni formato condicional use la columna; borrar es irreversible para los datos de la columna.
- Hojas auxiliares (consulta del usuario, 2026-11-12 18:55): sólo ahorran celdas si sus columnas viven únicamente allí; traerlas de vuelta a la maestra con fórmulas o enlaces vuelve a ocupar celdas. No hay ida y vuelta nativa; el servicio podría crear la fila auxiliar al confirmar el ID de la madre y copiar 2 o 3 columnas de contexto. Costo: ninguna vista ni reporte muestra en una misma fila columnas de las dos hojas, el equipo trabaja en dos lugares y las automatizaciones y reportes de esas columnas se mudan. Candidatos naturales: Facturación (unas 10 columnas, reporte Invoices) y Records (unas 9 a 12, reporte All Records Request); la maestra quedaría en unas 95 a 100 columnas (5 000 a 5 300 filas). Records por permiso exigiría una llave propia por fila. Alternativa: archivar proyectos cerrados (el servicio movería la familia completa; `Move rows` pierde la jerarquía), que choca con que el cliente vea lo cerrado. Recomendación: primero quitar columnas (112 a 118) y, si el crecimiento sigue, separar Facturación. Sin decisión.
- Revisión (2026-11-12 23:45 -05:00, sólo lectura por API; consulta del usuario "cuántas columnas"): el conteo anterior sólo sumaba Crown Castle y Blue Stream. Las otras hojas 2026 de clientes tienen 147 filas en total (Breezeline 38, Lightpath 39, Hotwire 21, Others 49, sin filtrar por fecha; la "Copy of 5. Lightpath" de 9 filas es copia y no cuenta): un año con todos los clientes cierra en unas 4 250 filas. Con eso caben como máximo 117 columnas sin margen; con margen para un 10 a 15 % de crecimiento anual, unas 105.
- Dependencias en reportes de `Producto/Reports` (columnas leídas por API): `Permitting` usa `Runner Pick up` (de la lista "sin uso"; casi siempre vacía), `Runner Submitting` y `Permit Coordinator Approved Date (QC)` (de "uso mínimo") y 9 columnas de días (`Record # Days`, `Prepare Packages # Days`, `App Delay Days from Contractor`, `Process # Days`, `Permit # Days`, `Design - Days in 1st Revision`, `Design - Days in 2nd Revision`, `Permit - Days in 1st Revision`, `Permit - Days in 2nd Revision`, `Permit - Days in Submitted`); `Invoices` usa `Aerial` e `Invoice # Days`; `All Records Request` usa `Record # Days`. Ningún reporte usa `Project # Days`, `QC # Days`, `PM Approval Days`, `Design Completed Days`, `Design MOT # Days` ni `As-built # Days`.
- Propuesta (sin decisión): unas 107 columnas, quitando 33: las 11 sin uso, 10 de uso mínimo (todas menos `Aerial`, que está en Invoices), las 6 nuevas por confirmar y las 6 columnas de días que ningún reporte usa. Quedarían unas 4 670 filas de capacidad (10 % sobre 2026). Si `Tone Locating`, `Survey Certified`, `Additional Site Survey`, `Sonde FTG` y `GPR` se facturan, unirlas en una columna de texto `Other Services` en vez de perderlas (108 columnas). Para 2027 con más crecimiento, la siguiente palanca sigue siendo separar Facturación.
- Consulta (2026-11-13 00:10 -05:00): 2 o 3 hojas hijas que reciban cambios de la maestra y le devuelvan los suyos. Respuesta: una celda ocupa espacio en la hoja donde está, aunque su valor venga de otra; si todo va y vuelve, la maestra conserva las mismas columnas y no ahorra nada. Sí ahorra un diseño en estrella: cada grupo de columnas vive sólo en su hoja hija; la hija trae 2 a 4 columnas de contexto de la maestra por fórmula entre hojas (cuestan celdas en la hija, no en la maestra); a la maestra vuelve como mucho una columna resumen si el equipo la necesita (por ejemplo `Invoice Status`). La fila hija la crea el servicio al confirmarse el ID de la madre, con `Tracking Project` como llave, y la actualiza si cambia el cliente (como hoy con `Linked Tracking`); "Copy rows" nativo no sirve porque agrega a la hoja destino las columnas que le faltan. Sincronización completa en los dos sentidos: no es nativa (Bridge, de pago) y con el servicio exige backend siempre encendido, resolver conflictos y evitar bucles y avisos duplicados; no recomendada. Cuentas: sólo hojas hijas, sin limpiar (140 menos unas 22 columnas de Facturación y Records), quedan unas 118 columnas y 4 240 filas, que no alcanzan para 2026; limpiar las 33 primero (107) y después separar Facturación (unas 12) deja unas 95 columnas y 5 260 filas. Facturación es la candidata más limpia (por proyecto, reporte Invoices); Records va por permiso (llave por fila) y sus columnas están también en el reporte `Permitting`. Falta saber quién llena las columnas de factura y de metraje.
- Análisis completo (2026-11-13 00:30 -05:00, pedido por el usuario antes de decidir; verificado el 2026-11-13 09:10 desde el equipo Linux, AC-27 y AC-28): `ANALISIS_COLUMNAS_KMV.md` (AC-01 a AC-26), con las 12 hojas originales 2025 y 2026 de los 6 clientes. Cambia dos supuestos: un año con todos los clientes ronda las 4 200 filas con crecimiento de 6,6 % (no 10 a 15 %), y la facturación también se llena en las hijas (85 a 89 %), así que una hoja de Facturación necesita llave por fila, igual que Records. El metraje lo llena diseño (dicho por el usuario) y se queda en la maestra. Propuesta: 107 columnas; plan B, Records aparte. Sin decisión.

Decisiones y propuesta (2026-11-13 09:25): las 6 columnas nuevas y las cantidades de servicios se quedan (AC-29); 9 columnas nunca usadas en 2026 (AC-30); propuesta del usuario de Records en hoja aparte con `Records Needed` en la maestra (AC-31) y cuentas de capacidad (AC-32). Sin decisión de borrar.

### PEN-46 Conversaciones de cada fila compiladas en una columna (reemplazo de Obs)

Prioridad: media. Alcance: backend. Estado: en uso en Pruebas (2026-11-12, SPEC-B17); prueba real correcta en PROJECT KMV.
Situación: la descarga CSV de una Dynamic View trae los datos de las filas pero no sus conversaciones (comentarios), comprobado por el usuario y reportado en la comunidad de Smartsheet. Al exportar una hoja o un reporte a Excel los comentarios van a otra pestaña, referidos por número de fila de Smartsheet y no junto a cada fila.
Nativo: la columna de sistema "Latest Comment" muestra el último comentario de cada fila (sólo el último); falta comprobar si sale en la descarga CSV de la vista.
Tipo (ADR-B15): Smartsheet no exporta cada fila con su conversación completa al lado; el backend puede hacerlo leyendo las conversaciones por API.
Pedido del usuario (2026-11-12): dejar de escribir el avance en `Obs` (texto largo con entradas `MM.DD - texto`, incómodo) y usar las conversaciones de cada fila en la Dynamic View; los clientes reciben la vista y, si no entienden el chat, descargan CSV o Excel con todo el historial listo, como hoy se ve `Obs` en el reporte de seguimiento del cliente.
Propuesta revisada: el servicio compila la conversación de cada fila en una columna de la hoja (formato `MM.DD - texto`, más reciente arriba, como `Obs`). Así la descarga CSV de la vista y la exportación a Excel del reporte la incluyen sin pasos extra, y la vista la muestra de sólo lectura.
Detalles: sondeo de conversaciones (`lastCommentedAt`) cerca de cada minuto y lectura sólo de las cambiadas; recompilación completa periódica para ediciones y borrados; escribir sólo filas cambiadas (cada escritura figura como del administrador en `Modified By`, SPEC-B08); límite de 4 000 caracteres por celda: se recortan las entradas más antiguas con una nota; sólo en Pruebas (PROJECT KMV).
Decisión del usuario (2026-11-12): reutilizar `Obs`, sin columna nueva.
Regla propuesta: agregar sin reemplazar. Cada comentario nuevo se antepone una sola vez a `Obs` como `MM.DD - texto` (comentarios ya incorporados registrados en PostgreSQL como estado técnico); el texto existente y lo que alguien siga escribiendo a mano se conservan. Editar o borrar un comentario después no cambia `Obs`. Comentarios que empiezan con `#interno` no se copian. Sin autor. Al superar 4 000 caracteres, la parte más antigua pasa a un comentario de la fila marcado por el servicio (que el servicio ignora) y no se pierde.
Carga estimada: el límite de la API es 300 llamadas por minuto por token; hoy el monitor usa unas 12 por minuto (versión cada 5 s). Listar conversaciones de una maestra de 3 000 filas son a lo sumo unas 30 páginas por ciclo. Antes de construir, comprobar si un comentario nuevo cambia la versión de la hoja; si la cambia, sólo se consultan conversaciones cuando hubo cambios.
Autorizado por el usuario (2026-11-12): escribir `Obs` en PROJECT KMV con los chats existentes; `APP_OBS_SYNC_ENABLED=true` en `.env`. Hecho: SPEC-B17, código (`services/obs/`), migración 004 y pruebas simuladas. Hallazgo: la API sigue listando conversaciones de filas borradas (106 comentarios en 49 filas, 7 vigentes); se ignoran.
Prueba real (2026-11-12 14:39): el usuario aplicó la migración 004 y reinició el backend; la primera pasada copió 61 comentarios en las 7 filas vigentes de PROJECT KMV, sin archivar ni errores, con el texto previo de `Obs` conservado debajo; la pasada siguiente no escribió nada. Falta: que el usuario confirme el resultado en la hoja y limpie los `Obs` con chats de prueba cuando termine.
Ampliación (2026-11-12, pedido del usuario): un chat que empieza con `**` es título de sección; queda arriba sin fecha y los mensajes siguientes entran debajo (SPEC-B17 OB-16, CA-08). Prueba real correcta (2026-11-12 15:20).

### PEN-47 Tracking Project cambia con el cliente y coherencia madre/hija

Prioridad: alta. Alcance: ID Manager y Smartsheet. Estado: implementada (2026-11-12 17:50, SPEC-ID01 ID-44 a ID-48); migración 005 aplicada y backend reiniciado por el usuario; salida de hijas de otro cliente y cambio de cliente de una madre con sus hijas comprobados en real. Origen: requisito del usuario (2026-11-12 17:30); falta decidir el comportamiento de las hijas y de las referencias antes de especificar (SPEC-ID01) y programar.
Requisito del usuario: el Tracking Project debe cambiar siempre que cambie `Customer`. Hoy no ocurre por diseño: un ID confirmado es permanente aunque cambien fecha, cliente o padre (SPEC-ID01 ID-34), y la fórmula de `Tracking Project` muestra el Stable ID si existe.
Revisión de PROJECT KMV (2026-11-12 17:30, sólo GET; 12 filas: 4 madres, 8 hijas; sin errores de fórmula; ID Manager con 4 `already_stable` y 8 `child_inherited`):
- Hijas de `KMV-BS-26-008` (Blue Stream) con otro cliente: una `HC-Hotwire Communications` y otra `CC-Crown Castle`. Conservan `KMV-BS-26-008` y su `Client Access` es el de Hotwire y Crown Castle: la vista de ese cliente mostraría una fila con ID de Blue Stream y `Client | Status Update` le escribiría sobre `KMV-BS-26-008`. El procesador no lo detecta.
- Madre `KMV-BS-26-008` sin `Project Name` ni equipo; sus hijas tienen nombres distintos entre sí, otra `Date Received` (11-12 frente a 11-11) y una sin fecha.
- Hijas con estados de madre (`COMPLETE`, `IN PROGRESS`): quedan sin `Phase`. Los estados en mayúsculas de las madres tampoco tienen `Phase` en el catálogo.
- `Linked Tracking` de la madre `KMV-CC-26-001` apunta a `KMV-BS-26-002`: otro cliente y no existe en la hoja (`ERROR: DIFFERENT CUSTOMER`).
Propuesta para la madre: si el código de cliente de su Stable ID ya no coincide con `Customer Code`, el procesador le asigna el siguiente número libre del nuevo cliente y año, retira el anterior (nunca se reutiliza, ID-32) y las hijas heredan el ID nuevo. Si vuelve al cliente original, recupera su ID anterior en lugar de gastar otro número. Queda rastro en la auditoría de PostgreSQL.
Por decidir: qué pasa con una hija cuyo cliente difiere del de su madre; si se deja nota del ID anterior en la fila; si las `Linked Tracking` que apuntaban al ID anterior se actualizan solas.
Funcionamiento actual explicado al usuario: `Project Number` propone `máximo Frozen Number del cliente y año + posición entre las madres sin Stable ID` (por `Row Order`); `Tracking Project` muestra el Stable ID si existe, el de la madre en una hija o el propuesto; el servicio decide con PostgreSQL y escribe `Stable Tracking Project` (oculta y bloqueada). Una madre copiada conserva el ID unos segundos y luego recibe otro (ID-42); sus hijas copiadas quedan en conflicto.
Alternativa más limpia, aprobada por el usuario el 2026-11-12 (ID-48): el código decide y la fórmula sólo muestra. Mientras no hay Stable ID, `Tracking Project` muestra `Pending ID` en lugar de un número provisional que puede cambiar; se deja de depender de `Project Number` y `Frozen Number`; el servicio asigna el siguiente número libre y detecta cambio de cliente, copias e hijas incoherentes. Costo: el ID aparece a los 5 a 15 s (ID-43) y, con el backend apagado, las madres nuevas quedan en `Pending ID`.
Decisiones del usuario (2026-11-12 17:50): al cambiar de cliente se reinicia todo y se da un número nuevo, también al volver al cliente original; las copias de madres e hijas no son casos especiales; la nota la decide el asistente (primero un comentario `#internal`; retirado el mismo día porque el usuario no quiere nada técnico a la vista: el rastro queda sólo en PostgreSQL y el log); corregir los errores, incluidas las `Linked Tracking` hacia el ID anterior. Hecho: SPEC-ID01 ID-44 a ID-48, `family.py`, `customer_change.py`, retiro en `store.py`, migración 005, interruptor `IDS_CUSTOMER_CHANGE_ENABLED` (activado en `.env`), fórmula de `Tracking Project` con `Pending ID` aplicada en PROJECT KMV y 5 pruebas nuevas. Al reiniciar, las dos hijas de otro cliente de `KMV-BS-26-008` saldrán de la jerarquía y recibirán su propio número.
Prueba real (2026-11-12 17:58, lectura por API y PostgreSQL): las dos hijas de otro cliente de `KMV-BS-26-008` quedaron en primer nivel debajo de esa familia con `KMV-CC-26-004` y `KMV-HC-26-001` (reservadas y confirmadas a las 17:56), con su nota `#internal`; el procesador queda con 6 madres `already_stable` y 6 hijas heredadas; `id_retirado` existe y está vacía. `KMV-CC-26-003` ya estaba usado por una fila borrada antes, por eso Crown Castle tomó 004 (ID-32: nunca se reutiliza).
Prueba real de madre (2026-11-12 18:04): el usuario cambió el cliente de `KMV-BS-26-008` a LP; el procesador retiró `KMV-BS-26-008` (`id_retirado`, auditoría `retirado` 18:00:37), reservó y confirmó `KMV-LP-26-001` y sus dos hijas tomaron el cliente LP y ese ID sin salir de la jerarquía; ciclo siguiente sin acciones.
Ajuste (2026-11-12 18:32, pedido del usuario): `Pending ID` también al instante cuando cambia el cliente, en una madre copiada y en una hija de otro cliente (SPEC-ID01 ID-49), para no mostrar un ID erróneo durante los segundos que tarda el servicio.

### PEN-48 Hoja de trabajo nueva: PROJECT KMV 1.0.0

Prioridad: alta. Alcance: ID Manager, Obs, catálogo y Smartsheet. Estado: hecho en el servicio (2026-11-13 09:59); falta que el usuario arranque el backend y apunte reportes y vistas a la copia. Pedido del usuario (2026-11-13 09:50); plan propuesto, falta su confirmación.
Pedido: desde ahora se trabaja en la copia `PROJECT KMV 1.0.0` (id `8346710503018372`, `Pruebas/Producto/PROJECT KMV`); el usuario borrará allí las columnas sin uso y desde ella se construyen las hojas hijas (PEN-49).
Estado de la copia (sólo GET): 140 columnas, 14 filas (8 madres) con los mismos Stable IDs que PROJECT KMV, fórmulas y 8 referencias en estado OK; automatizaciones copiadas: `Client | Status Update`, `DV | New Task Designer1`, `Designer2` y `Permitting Team` activas, `alert` y `Alertas` inactivas; no se copiaron `Auto | LT Records al llenar Record ID` ni `Auto | LT Records al cambiar Records Status`; 68 comentarios en 8 filas, con ids nuevos.
Plan propuesto: hacer configurable la hoja maestra del servicio (hoy constante `PRESENTABLE` en `ids/pilot.py`); script de migración con respaldo, ejecutado por el usuario con sudo, que pasa las 14 asignaciones de las filas de PROJECT KMV a las filas de la copia con el mismo Stable ID (`galp_ids` no puede cambiar `hoja_id` ni `fila_id`); marcar los 68 comentarios de la copia como ya copiados en `obs_comentario` para no duplicar `Obs`; apuntar el servicio a la copia; PROJECT KMV deja de vigilarse y queda como está. A cargo del usuario en la interfaz: alcance de los 5 reportes de `Producto/Reports`, Dynamic Views nuevas sobre la copia y el enlace a la vista de clientes en `Client | Status Update`. Las ediciones en la copia ya disparan los avisos copiados.

Hecho (2026-11-13 09:59, autorizado por el usuario): `IDS_MASTER_SHEET_ID` en la configuración (por defecto la hoja anterior) y `pilot.PRESENTABLE` lo lee; `services/ids/rehome.py` (plan puro y transacción) y `servicios/ids/mover_hoja_maestra.py` (simulación por defecto, `--confirmar`, respaldo en `~/galp_backups`, se niega con el procesador activo). Backend detenido por el asistente; traslado aplicado: 8 madres de PROJECT KMV a PROJECT KMV 1.0.0 (auditoría `inicializado`), 68 comentarios de la copia marcados en `obs_comentario`, 7 asignaciones de filas borradas siguen en la hoja anterior; `IDS_MASTER_SHEET_ID=8346710503018372` en `.env`. Simulación del procesador sobre la copia: 8 `already_stable`, 6 `child_inherited`, nada pendiente; Obs sin pendientes. PROJECT KMV ya no se vigila. Sin escritura en Smartsheet.

### PEN-49 Hojas hijas de Records y Facturación

Prioridad: media. Alcance: servicio y Smartsheet. Estado: Records en uso en Pruebas, prueba real correcta (2026-11-13 10:20); implementada (2026-11-13 10:10, SPEC-B18) y activada en `.env`; falta reiniciar el backend y la prueba real. Facturación, después de ver cómo funciona Records. Origen: propuesta del usuario (2026-11-13 09:50); diseño en `ANALISIS_COLUMNAS_KMV.md` AC-31, AC-33 y AC-34; depende de PEN-48.
Records: en la maestra sólo `Records Needed` (Yes/No); el servicio crea y mantiene la fila en la hoja de Records. Decidido por el usuario (2026-11-13 09:59): `Designer2` pasa a la hoja de Records como responsable (se renombrará después) y se suman `Date Received` y el contador `Record # Days`. Columnas según la captura del usuario: `Tracking Project`, `Agency`, `Project Name`, `Project Address`, `City`, `County`, `Send Method`, `Record Request`, `LT Records`, `Future Project #`, `PRR #`, `Security Key`, `Record Received`, `Records Status`, `Record Box` y `Record # Days`; faltan las fechas y a quién se asigna. Facturación: casi toda fila con ID tiene su fila; en la maestra queda `Invoice Status` como resumen.
Contadores de días (pregunta del usuario): cada hoja hija lleva sus propios contadores como fórmula sobre sus propias fechas (`Record # Days` en Records, `Invoice # Days` en Facturación). Los contadores de diseño y permisos dependen de fechas de la maestra; llevarlos a otra hoja exige una llave por fila en la maestra o que el servicio escriba los valores a diario, así que se quedan en la maestra por ahora.
Hecho (2026-11-13 10:10, autorizado por el usuario): hoja `Records Requests` (`7578012825636740`) en `Pruebas/Producto/PROJECT KMV` con 23 columnas (contexto bloqueado, `Master Row` oculta y bloqueada, desplegables con las opciones de la maestra, fórmulas de `Email Designer2` y `Record # Days`, 3 referencias al directorio en estado OK); casilla `Records Needed` en PROJECT KMV 1.0.0 (columna 28); `services/records/` (reglas y paso del procesador), `last_records_sync` en el estado, `APP_RECORDS_*` en la configuración. Vista previa real sin escrituras: 14 filas en la maestra, ninguna marcada, hoja hija vacía, se copiarían 12 columnas iniciales.
Quitar las columnas de Records de la maestra (consulta del usuario, 2026-11-13 10:13; sólo lectura): saldrían 14 (las 12 de Records más `Designer2` y `Email Designer2`); queda `Records Needed`. Dependencias en PROJECT KMV 1.0.0: fórmula `Designers List` (usa `Designer2`); aviso `DV | New Task Designer1` (incluye `LT Records` y `Record Box`); aviso `DV | New Task Designer2` (se muda a Records); reportes All Records Request (10 columnas), Permitting (Record Request, Record Received, Record # Days, Record Box) y MOT y Paquetes (`Designer2`); `APP_DESIGNER_COLUMNS` del backend. Orden propuesto: probar Records; migrar marcando `Records Needed` en filas con datos de Records; ajustar dependencias; borrar. Resultado con las 9 sin uso y las 2 auxiliares: unas 116 columnas (4 310 filas). Pregunta abierta: si `Designer2` también se usa para MOT y paquetes.
Prueba real (2026-11-13 10:20, lectura por API): el usuario reinició el backend y marcó `Records Needed` en 9 filas (madres e hijas); la hoja de Records tiene 9 filas, una por fila marcada, sin duplicados, con el contexto igual a la maestra; 5 conservan los valores iniciales copiados (por ejemplo `Designer2`, `LT Records` y `Records Status`) y en 4 el usuario llenó después los datos de Records en la hoja hija, que ya es la fuente. Procesador sin errores y `last_records_sync` en reposo.
