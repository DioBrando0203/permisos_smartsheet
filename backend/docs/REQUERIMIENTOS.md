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

Resumen al 2026-10-12:
- Terminadas: PEN-00, PEN-01, PEN-02, PEN-03, PEN-05, PEN-16 y la base de PEN-18 (SPEC-B07).
- Parciales: PEN-04 y PEN-11 (hechos y probados con Smartsheet simulado; ejecución real bloqueada por el modo solo lectura hasta PEN-07).
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

Prioridad: alta. Alcance: frontend y backend. Estado: listo para empezar (documentación completa el 2026-10-16).
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

Prioridad: media. Alcance: proyecto. Estado: propuesta (2026-10-16); exige ADR y OAuth (PEN-08) antes de escribir.
Contexto: el usuario evalúa Jira y Salesforce por sus conectores de pago. Smartsheet sigue como fuente de verdad; nuestro servicio sólo agrega lo que no da bien.
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

Prioridad: media. Alcance: configuración. Estado: pendiente; requiere decisión del usuario.
Situación: `APP_CLOSED_STATUSES` usa una lista inicial supuesta. En la cuenta real la fase 4 (Permit) concentra el trabajo "abierto"; si estados como "4. Permit Approved" significan trabajo terminado para el diseñador, la carga está inflada.
Hacer: que el usuario indique qué estados son cerrados para el diseñador; actualizar `.env` y RESULTADOS.

### PEN-28 Activos asociados a personas y contactos

Prioridad: media. Alcance: backend y frontend. Estado: en curso (2026-10-28, solicitado por el usuario).
Situación: el detalle de persona sólo muestra permisos de hojas. Smartsheet también expone reportes, dashboards, workspaces y carpetas; el backend aún no lista ni obtiene sus permisos o relaciones con hojas.
Hecho: definidas SPEC-B13 y SPEC-10. Hacer: extenderlas a todos los activos, crear endpoint de sólo lectura con caché, fixtures sintéticos y pruebas; después la sección de frontend en el detalle de persona. No se debe inferir acceso a un activo desde una hoja sin que la API lo confirme.

### PEN-12 Exportar

Prioridad: baja. Alcance: backend y frontend. Estado: terminada (2026-10-16): `GET /api/export/access.csv`.
Hacer: exportar a CSV la matriz persona por hoja con niveles. El archivo contiene correos reales: se genera bajo demanda y no se guarda en el servidor.

### PEN-29 Mapa de vías, milepost, jurisdicción y parcelas

Prioridad: media. Alcance: backend y frontend. Estado: en curso (2026-10-30): M1 a M4 implementadas; M5 y M6 pendientes. ADR-B16 y ADR-B17 aprobadas por el usuario.
Tipo (ADR-B15): (a) ni Smartsheet ni OSP dicen el milepost, de quién es la calle y qué parcela hay en un punto sin dibujar una solicitud en OSP; el mapa sólo consulta y no cambia cómo se pide el permiso.
Situación: verificado con GET reales que los servicios públicos del FDOT y de FDACS reproducen los valores de OSP (SR 953, vía 87281000, sección 281, milepost 3.124 a 3.839) y dan ciudad, condado, ZIP y parcela en Broward, Palm Beach, Martin y Miami-Dade. Investigación en `future_docs/`.
Specs: SPEC-B14 (backend) y SPEC-11 (frontend); ADR-13 del frontend (Leaflet).
Fases:
- M1 backend punto: transporte GIS sin token, cliente, catálogo de capas, reglas puras (milepost, jurisdicción, usos DOR), `GET /api/map/point`, `GET /api/map/sources`, pruebas con `respx` y verificación manual.
- M2 backend tramo: `GET /api/map/segment` con `osp_row` y geometría.
- M3 frontend punto: destino "Mapa" en la navegación, `/mapa`, mapa base USGS, clic o coordenadas, panel con vía, jurisdicción, ubicación, parcela y fuentes.
- M4 frontend tramo: dos clics, tramo resaltado y "Copiar para OSP".
- M5 adaptadores de condado: Palm Beach (`RESP_AUTH`); Broward, Martin y Miami-Dade según MJ-PEN-01 a MJ-PEN-03.
- M6 extras: capas de vías dibujadas, búsqueda por dirección, Turnpike (GIS-PEN-01) y mapa base de Esri con clave.
Límites: la jurisdicción de calles locales es aproximada hasta M5; USGS sólo tiene teselas hasta el zoom 16 en Miami (verificado), por lo que el detalle de calle se ve ampliado y algo borroso hasta M6.
