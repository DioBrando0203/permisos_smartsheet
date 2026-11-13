# Resultados verificados (backend)

Sólo ejecuciones reales, con entorno y hora de Lima (QB-10). Sin nombres ni correos de personas.

## 2026-10-12 11:10 -05:00 Exploración de la API con el token (sólo lectura, con curl)

Entorno: Linux, Python 3.14.4, Node 24.21.0.
- `GET /2.0/users/me`: 200; administrador del sistema de la cuenta.
- `GET /2.0/sheets?includeAll=true`: 200; 100 hojas.
- `GET /2.0/sheets/{id}/shares?include=workspaceShares`: 200; 13 permisos (12 `ITEM`, 1 `WORKSPACE`) en la hoja de muestra.
- `GET /2.0/shares?assetType=sheet&assetId={id}`: 200; `{"items": [...]}` con 12 permisos `ITEM`; ids de usuario como texto; `name` ausente en algunos.
- `GET /2.0/shares?...&sharingInclude=ITEM,WORKSPACE`: 200; 13 permisos. `sharingInclude=ALL` responde 400 (`errorCode` 1018; valores aceptados `ITEM`, `WORKSPACE`, `SUBJECT_DETAILS_PROFILE_IMAGE`).
- `GET /2.0/shares/{shareId}?assetType=sheet&assetId={id}`: 200.
- `GET /2.0/groups`: 2. `GET /2.0/users`: 4.

## 2026-10-12 12:40 -05:00 Backend implementado: suite y lectura real

Entorno: Linux, Python 3.14.4 en `.venv`; fastapi 0.143.0, httpx 0.28.1, pydantic 2.14.1, respx 0.23.1, ruff 0.17.0 (`requirements.lock`).
- `pytest`: 53 pruebas aprobadas en 0,82 s.
- `ruff check app tests`: sin errores. `ruff format --check app tests`: 39 archivos formateados.
- Módulo más grande: `services/shares.py` con 235 líneas.

Servidor `uvicorn app.main:app --env-file .env --port 8710 --reload`, `APP_READ_ONLY=true`, cuenta real:
- `GET /api/health`: `configured`, `read_only: true`.
- `GET /api/me`: administrador del sistema.
- `GET /api/sheets?q=hotwire`: total 100, 2 coincidencias, `can_manage_shares: true`.
- `GET /api/sheets/{id}/shares`: 13 permisos; propietario (propio y heredado) bloqueado; 11 editables.
- `GET /api/contacts`: 44.
- `GET /api/users`: 49 entradas (36 con acceso, 13 contactos sin acceso, 4 de la organización, 1 dueño del token), sin hojas fallidas; primera carga 3,3 s, desde caché 0,02 s.
- POST, PATCH y DELETE: 403 `READ_ONLY_MODE`; Origin ajeno: 403 `ORIGIN_NOT_ALLOWED`. En el log del servidor: 0 escrituras hacia Smartsheet y 0 apariciones del token.

## 2026-10-12 13:25 -05:00 Alcance de lectura de la cuenta (sólo lectura, con curl)

- `GET /2.0/sheets` (`includeAll`, `pageSize=1000` o `page=2`): siempre 100; son las hojas propias o compartidas con el token.
- `GET /2.0/users/sheets` (hojas de toda la organización, administrador del sistema): con `includeAll=true` devuelve 100 y `totalPages=-1`; con `pageSize=1000`, 104. Las 4 que no están en `/sheets` son de otros usuarios de la organización.
- `GET /2.0/shares?assetType=sheet&assetId=…` de esas 4 hojas: 200; el administrador puede leer sus permisos.
- `GET /2.0/users?include=lastLogin`: agrega `lastLogin` y ya trae `sheetCount`.
- `GET /2.0/workspaces`: 4. `GET /2.0/reports`: 136. `GET /2.0/sights` (dashboards): 39.

## 2026-10-12 14:10 -05:00 Auditoría, comparación y operaciones masivas

- `pytest`: 71 pruebas aprobadas en 1,20 s. `ruff check` y `ruff format --check`: sin observaciones.
- Cuenta real, `APP_READ_ONLY=true`:
  - Auditoría del plan 2026 (por código de permalink): 30 accesos, 26 externos, 13 sin nombre, 3 fuera de contactos. Alertas: `EXTERNAL_CAN_SHARE` 3, `PERSONAL_EMAIL_CAN_EDIT` 16, `UNNAMED` 13, `NOT_IN_CONTACTS` 1.
  - Comparar 2025 con 2026: 3 sólo en 2025, 5 sólo en 2026, 2 con distinto nivel (`EDITOR_SHARE` a `EDITOR`, `EDITOR` a `ADMIN`), 22 iguales.
  - Resumen `q=crown castle`, `inactive_days=180`: 11 hojas; de 8 personas (2019, 2020) a 28 (2026), sin contar al propietario; sólo "Sprint 2019" marcada inactiva.
  - Copiar 2025 a 2026 (simulación): 3 `CREATE`, 23 `KEEP`, 1 `SKIP`; con `upgrade_levels`: 1 `UPGRADE`.
  - Revocar (simulación) a una persona que sólo está en 2025: 26 `REMOVE`.
  - Ejecutar copia: 403 `READ_ONLY_MODE`. Log del servidor: 0 escrituras hacia Smartsheet.

## 2026-10-12 14:45 -05:00 Revisión de riesgos de la cuenta

- `pytest`: 75 aprobadas. `ruff check` y `ruff format --check`: sin observaciones.
- Cuenta real, `GET /api/review`: 100 hojas en 4,6 s (primera lectura), 0 fallidas.
  - `min_severity=medium`: 47 hojas con alertas; 20 personas con correo personal y edición; 9 externas que pueden compartir.
  - `min_severity=high`: 18 hojas; las 9 externas que pueden compartir lo hacen en 10, 8, 6, 2, 2, 1, 1, 1 y 1 hojas. Hojas con más: planes 2026 de Lightpath, Blue Stream y Breezeline (4 cada una).
  - Log: 0 escrituras hacia Smartsheet.

## 2026-10-16 -05:00 Arranque con iniciar.py

- `pytest`: 78 aprobadas (3 nuevas en `test_launcher.py`). `ruff check` limpio, incluido `iniciar.py`.
- Real: con el 8710 ocupado por una instancia previa del usuario, `python3 iniciar.py` arrancó en 57743 y una segunda vez en 41281; `/api/health` respondió en ese puerto y un DELETE con `Origin` de ese puerto llegó a `READ_ONLY_MODE` (Origin aceptado). Instancias de prueba detenidas; la del usuario en 8710 no se tocó.

## 2026-10-16 -05:00 Fuentes de actividad (quién cambió qué, sólo lectura con curl)

- `GET /2.0/events` (Event Reporting): 403, `errorCode` 1013 "not supported by your plan". No hay registro de eventos de la cuenta (permisos, borrados, accesos) por API en este plan.
- `GET /2.0/sheets/{id}/rows/{rowId}/columns/{columnId}/history`: 200; cada cambio con `value`, `displayValue`, `modifiedAt`, `modifiedBy`. Una solicitud por celda.
- `GET /2.0/sheets/{id}?include=writerInfo`: 200; cada fila con `createdAt`, `createdBy`, `modifiedAt`, `modifiedBy` (plan 2026: 2050 filas, 500 por página).

## 2026-10-16 -05:00 Actividad de una hoja (SPEC-B08)

- `pytest`: 87 aprobadas. `ruff check` y `ruff format --check`: sin observaciones.
- Rutas del "Registro de actividad": `/sheets/{id}/activity`, `/activityLog`, `/events` 404; `/events?assetType=sheet` 403 (plan). `/sheets/{id}/version`, `/updaterequests` y `/sentupdaterequests` 200 (no son registro de actividad).
- Cuenta real, plan 2026 (por código de permalink), `run.py` en 8710:
  - 30 días: 2052 filas, 2046 modificadas; últimos editores 1884, 160, 1 y 1 filas; 24 con edición sin ser último editor; 4,3 s (primera lectura, 5 páginas).
  - Una cuenta tocó el 92 % de las filas: se agregó el aviso de cuenta dominante (CA-08).
  - 7 días: 2042 modificadas, 3 editores. 365 días: 2052, 5 editores.
  - Historial de una fila: 55 columnas con valor, 0 fallidas, 105 cambios, 10,9 s.
  - Log: 0 escrituras hacia Smartsheet. Instancia de prueba detenida.

## 2026-10-16 -05:00 Webhooks y Event Reporting

- `/events` con `since`, `streamPosition` y `maxCount`: 403 1013 en las tres.
- `/webhooks?includeAll=true`: 400 1018 (`includeAll` retirado, B-09). `/webhooks?pageSize=100&page=1`: 200; 1 webhook `ENABLED`, alcance `sheet`, de Data Uploader de Smartsheet (`attachment.created`). Los webhooks están disponibles en el plan.

## 2026-10-16 -05:00 Paginación explícita (PEN-23)

- Comportamiento real: `/users/sheets` con `pageSize=100` da 100 + 14 y la página 3 vuelve con `pageNumber` 0 y vacía; `/sheets` con `pageSize=60` repite la página 2 al pedir la 3; `/contacts` acepta `pageSize=1000`. `/sheets` tiene ahora 110 hojas (10 creadas desde el 2026-10-12; `includeAll` también da 110).
- `pytest`: 90 aprobadas (3 nuevas de paginación).

## 2026-10-16 -05:00 Organización, última conexión, calidad de datos y CSV

- `pytest`: 103 aprobadas. `ruff check` y `ruff format --check`: sin observaciones. Sin caracteres de control ni invisibles en `app/`, `tests/` y `run.py`.
- Cuenta real, `run.py` en 8710:
  - `/api/sheets`: 114 (110 del token y 4 de otra persona); las 4 sin nivel; permisos de una ajena: 2, todos bloqueados.
  - Directorio `only=org`: `last_login` de los 4 usuarios: 2 conectados hoy, 1 el 2026-05-11 y 1 el 2026-06-29.
  - Calidad del plan 2026 (2053 filas, 2,3 s): `Record ID` 98 filas repetidas en 16 valores (el más repetido es el texto "By email", no un identificador) y 351 no numéricas; `Design Ticket` 4 repetidas; `Permit #` 106 repetidas en 37 valores; `Designer1` vacío en 1391 filas; `Project Status` vacío en 12.
  - CSV `q=crown castle`: 163 filas, BOM presente, 0 hojas fallidas, nombre `accesos-smartsheet-2026-10-16.csv`.
  - Log: 0 escrituras hacia Smartsheet. Instancia detenida.

## 2026-10-16 -05:00 Automatizaciones de Smartsheet (sólo lectura)

- `GET /2.0/sheets/{id}/automationrules`: 200. Plan 2026: 2 reglas de notificación, ambas apagadas, 0 destinatarios; una desactivada por Smartsheet con `NO_POTENTIAL_RECIPIENTS`.
- 110 hojas del token: 63 con automatizaciones, 80 reglas (79 notificaciones, 1 aprobación); 9 habilitadas y 71 apagadas; 15 apagadas por Smartsheet por `NO_POTENTIAL_RECIPIENTS`. Las 8 habilitadas "sin destinatarios explícitos" avisan a una columna (`recipientColumnIds`): sí tienen destinatario.
- Corregido el 2026-10-16 (ver la entrada de SPEC-B10): la hipótesis de que fallaban por `Designer1` (lista) era falsa; ninguna regla usa las columnas de diseñador.

## 2026-10-16 -05:00 Salud de las automatizaciones (SPEC-B10)

- `pytest`: 108 aprobadas. `ruff check` y `ruff format --check`: sin observaciones. `client.py` dividido en recursos (168 líneas) y `transport.py` (142) sin cambiar pruebas.
- Cuenta real, `GET /api/automations` (17 s, primera lectura): 110 hojas, 63 con reglas, 80 reglas, 0 fallidas. Estado: 9 `ok`, 71 `disabled`. Problemas: `DISABLED` 56 (apagadas sin motivo de Smartsheet), `DISABLED_NO_RECIPIENTS` 15, `NO_RECIPIENTS` 16, `RECIPIENT_COLUMN_NOT_CONTACT` 2.
- Columnas destinatarias: `Construction Manager` (contacto) 51, `Assigned To` 4, `Contacto responsable` 2, `Assignee` 1; de texto: `Current Assignee` 1 y `Construction Manager` 1. Ninguna regla usa `Designer1` ni `Designer2`: no hay alertas de asignación de diseñador.
- Plan 2026: "Alertas" (a `Construction Manager`) apagada a mano; "alert" sin destinatarios y apagada por Smartsheet.
- Log: 0 escrituras. Instancia detenida.

## 2026-10-16 -05:00 Referencias entre hojas (SPEC-B11)

- `pytest`: 112 aprobadas. `ruff check` y `ruff format --check`: sin observaciones.
- Cuenta real, catálogo "Source Designers" (25 diseñadores, columna `Designer`):
  - Plan 2026, `Designer1`: 662 filas con diseñador, 71 con un nombre que no está en el catálogo (4 personas y el texto "Designer1").
  - Toda la cuenta, `Designer1` (11,6 s): 14 hojas con la columna, 95 sin ella, 227 filas fuera del catálogo; el texto literal "Designer1" aparece como valor en 13 hojas (fila de encabezado copiada como dato).
  - Toda la cuenta, `Designer2` (2,8 s): 15 hojas, 705 filas fuera del catálogo; una persona concentra 557.
  - Log: 0 escrituras y 0 líneas de httpx con URL. Instancia detenida.

## 2026-10-16 -05:00 Carga y acceso de diseñadores (SPEC-B12)

- `pytest`: 117 aprobadas. `ruff check` y `ruff format --check`: sin observaciones.
- Cuenta real, `GET /api/designers` (13,8 s, primera lectura): 110 hojas, 15 con columnas de diseñador, 0 fallidas; 1249 asignaciones abiertas, 12 en espera, 1789 cerradas (con la lista inicial de cerrados); 13 filas de encabezado copiadas excluidas.
- 27 diseñadores: 18 identificados en el directorio por nombre, 0 ambiguos, 9 fuera del catálogo.
- 17 diseñadores tienen trabajo abierto en hojas que no tienen compartidas (entre 2 y 6 hojas cada uno).
- La fase 4 concentra la mayor parte del trabajo abierto: depende de qué estados se consideren cerrados (PEN-27).
- Hojas con más filas abiertas sin diseñador: planes 2026 de Crown Castle (409) y Blue Stream (293) y sus copias.
- Log: 0 escrituras. Instancia detenida.

## 2026-10-16 -05:00 F0 del backend para el frontend

- `pytest`: 128 aprobadas. `ruff check` y `ruff format --check`: sin observaciones.
- Build servido: rutas del panel a `index.html`, API y `/docs` intactos (`test_frontend.py`).
- Smartsheet falso: el backend completo funciona contra él (`test_fake_smartsheet.py`, 4 pruebas).
- Manual: `python -m tests.fake_smartsheet --port 8791` y `run.py` con `SMARTSHEET_BASE_URL` del falso y `SMARTSHEET_ACCESS_TOKEN=fake-token`: `/api/me` devolvió la cuenta de prueba, un PATCH quedó registrado en `/_fake/writes`, 0 llamadas a `api.smartsheet.com`, `.port` con 8710. Las variables de entorno ganan al `.env` (comprobado con `Settings()`).
- Cierre por SIGTERM: `.port` borrado y 8710 libre (tras la corrección de B-11).
# 2026-10-30 Mapa GIS (PEN-29, M1-M2)

- `pytest`: 137 pruebas aprobadas, incluidas 9 de mapa y reglas puras.
- `ruff check app tests` y `ruff format --check app tests`: sin observaciones.
- Verificación manual GET con backend en 8710: el tramo de control devuelve SR 953, vía `87281000`, sección `281`, mileposts `3.124` a `3.839` y las ocho fuentes en estado `ok`.
- Sólo lecturas GIS públicas; no se escribió en Smartsheet ni se mostró ni registró nombre de propietario.

## 2026-10-30 19:27 -05:00 Entorno Windows, buscador del mapa y GIS falso (PEN-29)

- Equipo nuevo (Windows 11): `backend/.venv` con Python 3.14.7, instalado con `pip install -c requirements.lock -e ".[dev]"`; mismas versiones que el lock salvo `uvloop` (no aplica en Windows) y `colorama` (dependencia de `click` en Windows).
- Con Python 3.12 la colección de pruebas falló al importar `app/services/sheets.py` (B-12); con 3.14.7 pasa.
- Antes de los cambios de esta sesión (código del commit "mapa mejorado", que agregó el buscador): `pytest` 151 aprobadas; `ruff check` y `ruff format --check` sin observaciones.
- Después: `pytest` 156 aprobadas (4 de `test_fake_gis.py` y 1 de `test_e2e_backend.py` nuevas); `ruff check app tests` y `ruff format --check app tests` sin observaciones.
- El GIS falso respondió las ocho capas del punto sin ninguna solicitud con `Authorization`; el buscador funcionó contra él por ruta con milepost, calle y dirección.
- No se hicieron GET reales del buscador a FDOT ni al Censo en esta sesión; no se escribió en Smartsheet.

## 2026-10-30 20:28 -05:00 Fuente caída sin espera larga y parcelas de Broward (PEN-30)

- Diagnóstico con el backend real: punto en Fort Lauderdale en 60,6 s; las siete capas del FDOT en menos de 1 s y `fdacs_parcels: timeout` (60 566 ms). `gis.fdacs.gov` resuelve por DNS pero no conecta (curl HTTP 000 a los 21 s); FDOT sí (B-13).
- Capa de parcelas de Broward (MJ-BR-01) consultada desde este equipo: responde, folio `494236110072` y `494236300010` en dos puntos de prueba.
- `pytest`: 160 aprobadas (4 nuevas en `test_map_fallback.py`); `ruff check app tests` y `ruff format --check app tests` sin observaciones.
- Manual tras reiniciar `run.py` (la recarga automática no terminó, B-14): primer punto 6,0 s (FDACS 5,6 s sin conexión, respaldo de Broward ok) y siguiente 1,6 s (FDACS saltado), ambos con folio y `source: broward_parcels`.
- Sólo lecturas GIS públicas; no se escribió en Smartsheet.

## 2026-10-30 21:11 -05:00 Trazo como en OSP (PEN-32) y contornos de parcelas (PEN-33)

- Verificado antes de programar: la capa 8 del FDOT acepta rectángulos (una línea con radio da 400); la capa 13 de Admin_Boundaries da D8/FTE sobre SR 821 y sólo D6 sobre SR 953; Broward (Parcels/FeatureServer/0) y Miami-Dade (MD_LandInformation capa 26) devuelven polígonos por rectángulo.
- pytest: 176 aprobadas (nuevas: 7 de test_trace_rules.py, 8 de test_map_trace.py y 2 de test_fake_gis.py); ruff check y ruff format --check sin observaciones.
- Manual con GET reales (backend reiniciado por B-14): trazo de control en 1,6 s con la fila de OSP (Miami-Dade, SR 953, 87281000, 281, 3.124 a 3.839, Turnpike false, LEJEUNE RD/NW 42 AVE); giro SR 953 a SR 968 en 1,4 s con dos filas (3.126 a 3.449 y 4.533 a 4.789); trazo en SR 821 con Turnpike true.
- Manual de contornos: Broward 41 parcelas, 1 300 vértices, 31 KB en 1,1 s; Miami-Dade 121 parcelas, 757 vértices, 22 KB en 0,8 s; sólo parcel_id y rings.
- No se escribió en Smartsheet; no se pidió ni registró ningún propietario.

## 2026-10-31 10:58 -05:00 Trazo ajustado a LRS oficial (PEN-35)

- `pytest`: 189 pruebas aprobadas. `ruff check app tests` y `ruff format --check app tests`: sin observaciones.
- `GET /api/map/trace` conserva `input_length_mi` para la polilínea marcada y calcula `length_mi` y cada `WorkLocation.length_mi` desde la geometría LRS oficial recortada entre mileposts.
- La comprobación fue simulada contra el GIS falso; no se consultó Smartsheet ni se realizó ninguna escritura.

## 2026-10-31 11:30 -05:00 Integridad de trazo y actualización (PEN-37)

- Python 3.14.4 en Linux. `pytest`: 205 aprobadas; Ruff check y format --check: limpios (123 archivos).
- Regresión reproducida antes de corregir: LRS sintética dividida en dos paths devolvía sólo MP 0.2–0.5 al pedir 0.2–0.8; una salida y regreso a la vía se unían en una fila sin aviso.
- GET manual real desde `/api/map/trace`, con `refresh=true`: control `25.771778,-80.263610;25.782147,-80.264005` y su inverso dan SR 953, MP 3.124–3.839, longitud 0.717 mi, cobertura 100 %, sin avisos.
- GET manual real de salida/regreso: `25.771778,-80.263610;25.775,-80.26375;25.777,-80.261;25.779,-80.2639;25.782147,-80.264005`: cobertura 57.2 %, 0.380 mi sin vía, `TRACE_PARTIAL`; filas SR 953 (3.124–3.353), vía local 87580500 (0.018–0.051) y SR 953 (3.615–3.839).
- Las lecturas reales consultaron sólo GIS público a través del backend activo con recarga; no hubo escrituras ni lecturas de Smartsheet. El caso de control reconstruye coordenadas desde MPs: no prueba igualdad independiente del ajuste OSP para entradas idénticas.

## 2026-10-31 12:40 -05:00 Ajuste de recorrido con datos reales (PEN-38) y cruces recortados (PEN-39)

- Python 3.14.4 en Linux. `pytest`: 220 aprobadas; Ruff check y format --check: limpios (128 archivos).
- `MapService.trace` contra el GIS real del FDOT (script local, sin HTTP ni Smartsheet), `snap=true`, `radius_m=100`:
  - control `25.771778,-80.263610;25.782147,-80.264005`: SR 953 sección 281, MP 3.124–3.839, 0.717 mi, ajuste 0.0/0.0 m; igual que en modo estricto.
  - control corrido 0.0005° al oeste (~50 m): `adjusted`, SR 953 MP 3.125–3.839, ajuste 50.0/50.1 m; el modo estricto daba la vía local 87049500 con `TRACE_PARTIAL`.
  - diagonal `25.782147,-80.264005;25.771676,-80.255605`: dibujo 0.893 mi, resultado 1.221 mi en SR 953 (3.118–3.839) y SR 968 (4.534–5.032), `TRACE_CONNECTIONS_INFERRED`.
  - Broward Blvd entre Andrews Ave y Federal Hwy: SR 842 MP 6.773–7.166; dibujado ~45 m al norte: `adjusted`, SR 842 MP 6.775–7.166 (el estricto daba tres vías locales incompletas); zigzag desde NW 7 Ave: SR 842 MP 6.336–7.166, 0.832 a 0.828 mi.
  - Respuestas entre 1.1 y 1.7 s sin caché; las seis fuentes respondieron.
- Buscador real en Fort Lauderdale: "Federal Hwy & Sunrise" no daba resultados; tras PEN-39 da `86020000` (US-1) en MP 1.975 y 1.027 y "Sunrise Blvd & Federal Hwy" además `86005000` en 0.0. "Las Olas & 3rd Ave" (0.258), "Broward Blvd & Andrews Ave" (6.773) y "NW 42 Ave & W Flagler St" (3.117) sin cambios. "Las Olas & Federal Hwy" sigue vacío: no hay cruce a nivel (túnel) y TIGER está bloqueado (B-15).
- Sólo lecturas de GIS público; ninguna lectura ni escritura de Smartsheet.
# 2026-11-03 10:23 -05:00 Validación de asociaciones (PEN-24)

- Backend: 222 pruebas aprobadas; `ruff check app tests` y `ruff format --check app tests` aprobados.
- Lectura real: 4 hojas del piloto identificadas; comparación exploratoria de Tareas contra Proyectos con 2 filas revisadas y 2 proyectos no encontrados. Columnas y reglas de relación pendientes de confirmar; sin escrituras.
# 2026-11-03 10:45 -05:00 Preparación de integración de IDs

- Backend: 229 pruebas aprobadas; Ruff y formato aprobados; sintaxis shell de respaldo/migración comprobada. PostgreSQL temporal, sin migrar ni inicializar la base real.
- Inventario piloto validado en memoria: 19 IDs. Historial de celdas actuales: 38 lecturas correctas; 4 valores históricos de proyectos no canónicos. Otras hojas candidatas: 55 revisadas, 48 con columna, 21 120 valores canónicos y 785 otros; sin garantía de historia completa. Ninguna escritura en Smartsheet.

# 2026-11-03 10:39 -05:00 Motor de reservas de IDs

- Backend: 226 pruebas aprobadas, Ruff y formato aprobados; pruebas de PostgreSQL 18 temporal con inicialización, rollback, auditoría, idempotencia y reservas concurrentes.
- GET reales: 19 IDs visibles canónicos y columnas estables no vacías en las cuatro hojas; 6 relaciones principales de Tareas revisadas sin problemas. No comprueba máximos históricos de filas eliminadas. Sin inicialización de la base real ni escrituras en Smartsheet.
# 2026-11-03 11:00 -05:00 Importación y simulación de IDs

- 233 pruebas aprobadas, Ruff y formato; importación repetida y DRY_RUN sin cambios verificados con PostgreSQL temporal.
- Lecturas reales comprobaron workspace, versiones y relaciones de 19 IDs; sin importación real ni escrituras en Smartsheet.
- Restauración aislada de respaldo previo a 002: dos tablas originales restauradas; no prueba respaldo posterior a la migración.
# 2026-11-03 11:15 -05:00 Simulación de tareas nuevas

- 11 pruebas específicas y 234 pruebas backend aprobadas; Ruff y formato correctos. DRY_RUN real: 19 IDs ya estables; no hubo reservas nuevas ni escrituras en Smartsheet.

# 2026-11-03 18:31 -05:00 Calles de St. Johns y lugares censales (PEN-40)

- Backend: 255 pruebas aprobadas (17 nuevas en `test_county_roads.py` y `test_map_county.py`). Ruff y formato aprobados en los archivos de PEN-40; los 13 avisos de Ruff y el de formato que quedan son de `app/api/router.py` y `app/api/routes/idsmart.py` (commit `84c7478`, ID Manager), ajenos a este cambio.
- GET reales con `python run.py` en 8710 (`/api/map/point?refresh=true`): King St, St. Augustine, `CITY` St. Augustine `high`; 8th St, St. Augustine Beach, `CITY` `high`; Tidestone Dr `COUNTY` St. Johns County `high`; UF Health Way `PRIVATE` `high`; Greyson Ct `SPECIAL_DISTRICT` `high`; US 1 S `FDOT` `high` con SR 5 del FDOT a 6,1 m; Nocatee pasa de `CITY` Nocatee a `place` Nocatee y `COUNTY` `unincorporated` `low` (sin calle del condado a 25 m). Caso de control SR 953 en Miami-Dade sin cambios y sin consultar al condado. `/api/map/sources` lista `stjohns_roads`.
- Script de punto con el servicio del backend (sin servidor): SR 9B en su extremo sur da `FDOT` `medium` (el tramo estatal del FDOT está a más de 25 m); Hastings da `COUNTY` `high` aunque el Censo la siga como municipio. Sin escrituras en Smartsheet.

# 2026-11-03 19:09 -05:00 Calles por jurisdicción, calles del trazo y tipo de municipio (PEN-41)

- Backend: 267 pruebas aprobadas (nuevas: `test_trace_streets.py`, `test_county_streets.py` y casos de city, town y village en `test_county_roads.py`); Ruff y formato aprobados fuera de `app/api/router.py` y `app/api/routes/idsmart.py` (ID Manager, ajenos a este cambio).
- GET reales con el servicio del backend: celda (-81.48, 30.08, -81.46, 30.10) con 99 tramos (58 condado, 32 privada, 5 FDOT, 4 sin dueño); trazo CR 210 W y Beachwalk Blvd: County Road 210 W 0.476 mi y Beachwalk Blvd 0.097 mi, ambos St. Johns County, 0.036 mi sin calle, fuente en 1,0 s. En esa zona la LRS del FDOT no tiene vías a 1,5 km (CA-36).
- GET reales por HTTP (`python run.py`, 8710): Jupiter `TOWN` "Town of Jupiter"; Wellington `VILLAGE` "Village of Wellington"; Miami y West Palm Beach `CITY`; St. Augustine `CITY` "City of St. Augustine" con `county_maintenance`. Sin escrituras en Smartsheet.
# 2026-11-04 12:14 -05:00 Política anual del ID Manager

- 289 pruebas backend aprobadas; Ruff y formato correctos. Pruebas de año desde fecha ISO, secuencias independientes, continuidad de 2026, procesamiento por dependencias y concurrencia con PostgreSQL temporal.
- DRY_RUN contra el piloto real: 19 IDs ya estables; base: 19 asignaciones, 12 secuencias y 19 eventos. Solo lecturas. Migración 003 pendiente.

# 2026-11-04 15:29 -05:00 Integración de escritura y procesador del ID Manager (PEN-24)

- Línea base antes de cambios: 289 pruebas aprobadas, Ruff y formato correctos.
- Después: 302 pruebas backend aprobadas (nuevas: `test_id_e2e.py` con 9 casos, tope del procesador y rutas `/audit`, `/recovery`, `/rows/assign`, `/processor/run`); Ruff y formato correctos.
- PostgreSQL real en solo lectura: 19 asignaciones confirmadas, 12 secuencias, 19 eventos; CHECK de auditoría con `confirmado` y `UPDATE(estado)` para `galp_ids`: migración 003 reconocida.
- Servicio real con `python run.py` en 8710: `/docs` 200; diez rutas `/api/ids/*`; sin token 401; status con barreras apagadas y modo simulación; database 19/19/12/19; dry-run, processor/run y conflicts con 19 `already_stable` y 0 conflictos; recovery vacío; health correcto; `rows/assign` 403 en piloto y fuera de lista; origen ajeno 403.
- Registro del servidor: 97 GET a Smartsheet, ningún PUT, POST ni DELETE, sin excepciones. Versiones de las cuatro hojas y conteos y secuencias de PostgreSQL idénticos antes y después.

# 2026-11-04 16:36 -05:00 Política de numeración y primera escritura real del ID Manager (PEN-24)

- 303 pruebas backend aprobadas; Ruff y formato correctos. Nuevos casos: registro de Stable ID sin rastro, renumeración al siguiente libre, `Reference` vacía, restauración de Stable vaciado, ámbito 2026 nuevo desde 001 y ID confirmado permanente ante cambio de fecha.
- DRY_RUN real previo: 19 `already_stable` y 4 `needs_reservation` con `proposed_id` igual a la fórmula y sin renumerar.
- Ciclo real del procesador (barreras sólo en el proceso, `.env` sin cambios): 4 `confirmed`: `KMV-LP-26-001`, `KMV-CC-26-721`, `KMV-CC-26-722` en Proyectos y `KMV-CC-26-720-01` en Tareas. Relectura: Stable y visible iguales en las cuatro filas.
- PostgreSQL: 23 asignaciones confirmadas, 14 secuencias (`project:KMV-LP-26` 1, `project:KMV-CC-26` 722), auditoría con 4 `reservado` y 4 `confirmado` nuevos (eventos 20 a 27).
- Segundo ciclo real: `outcomes` vacío, 23 `already_stable`; 23 asignaciones y 27 eventos sin cambios.

# 2026-11-04 16:56 -05:00 Catálogo de proyectos y Linked Tracking (SPEC-B16, PEN-24)

- 311 pruebas backend aprobadas (nuevas: `test_catalog_rules.py` y `test_project_catalog.py`, 8 casos); Ruff y formato correctos.
- Lectura real de Proyectos (Piloto), sólo GET: BS 2 proyectos, CC 5 actuales y 2 históricos (`KMV-CC-26-563`, `KMV-CC-26-627`, opciones curadas del desplegable), OT 1, LP 1, ZY 0. Linked Tracking: 1 `current_valid`, 2 `historical_valid`, 6 vacíos; coincide con la fórmula `Control Linked Tracking`.
- Plan de sincronización sin hoja catálogo: 11 `add`. `POST /api/catalogs/projects/sync` sin token: 401. Ninguna escritura.
- ID Manager después de los cambios: 23 asignaciones confirmadas y 27 eventos sin cambios; DRY_RUN con 23 `already_stable`.

# 2026-11-04 17:00 -05:00 Procesador automático de IDs en el servidor real (PEN-24)

- Servidor reiniciado por el usuario con `python run.py` en 8710: `/api/ids/status` con `processor_mode` `assign`, `processor_active` true, intervalo 60 s y máximo 5 filas.
- Primer ciclo automático: 23 `already_stable` y 1 `needs_reservation`; resultado 1 `confirmed`. Fila de Records: visible y Stable `KMV-CC-26-720-01-R1`; secuencia `record:KMV-CC-26-720-01` en 1.
- PostgreSQL: 24 asignaciones confirmadas; eventos 28 `reservado` y 29 `confirmado`. DRY_RUN posterior: 24 `already_stable`, 0 pendientes, 0 conflictos.
- Catálogo en el servidor real (GET): BS 2, CC 7 (2 históricos), OT 1; Linked Tracking: 1 actual válido, 2 históricos válidos, 6 vacíos.

# 2026-11-04 17:07 -05:00 Hoja catálogo de proyectos en Pruebas (SPEC-B16, PEN-24)

- Escritura autorizada por el usuario: hoja `Catálogo de Proyectos (Piloto)` (`8048198976491396`) creada en `Pruebas/Normalizacion de Datos - Piloto/01 Datos`; workspace comprobado `7965022790936452`.
- Sincronización real: `add` 11, `update` 0, `unchanged` 0, `conflict` 0; filas ordenadas BS, CC (incluye históricos 563 y 627), LP y OT. Versión de Proyectos 126 antes y después. Plan posterior: todo `unchanged`.
- 311 pruebas backend aprobadas (orden del catálogo incluido); Ruff y formato correctos. PostgreSQL: 24 asignaciones confirmadas, 29 eventos, sin cambios.

# 2026-11-04 17:24 -05:00 Selector de Linked Tracking vinculado y flujo automático (SPEC-B16, PEN-24)

- Linked Tracking vinculado por el usuario a `Catálogo de Proyectos (Piloto)`: opciones iguales a las 11 filas del catálogo y en el mismo orden; `validation` false; valores existentes conservados.
- Procesador tras el reinicio: `last_catalog_sync` con 11 `unchanged` antes de la prueba.
- Proyecto de prueba (OT-Others, 2026-11-04) creado por API: fórmula `KMV-OT-26-002`; Stable ID a los 45 s; catálogo a los 51 s (orden BS, CC, LP, OT); opción del desplegable a los 57 s. PostgreSQL: 25 asignaciones confirmadas.
- Pendiente de comprobación visual por el usuario: filtrado al escribir el código del cliente y `ERROR: DIFFERENT CUSTOMER` al elegir otro cliente.

# 2026-11-04 19:33 -05:00 Verificación desde el equipo Windows (PEN-24, SPEC-B16)

- Entorno: `pip install -c requirements.lock -e ".[dev]"` instaló `psycopg` 3.3.7, ahora dependencia obligatoria.
- 282 pruebas backend aprobadas y 29 omitidas por falta de PostgreSQL 18 local (B-16); Ruff y formato correctos (174 archivos).
- Backend local con `APP_READ_ONLY=true` y procesador apagado por variables del proceso, `.env` sin cambios: `/api/health` con `read_only` true. Detenido al terminar; 8710 libre.
- Catálogo (GET con `refresh`): 16 proyectos, BS 3, CC 10 (2 históricos), LP 1 y OT 2; sin duplicados. Plan de sincronización: 16 `unchanged`.
- Linked Tracking: 2 `current_valid`, 2 `historical_valid`, 9 vacíos y 1 `other_customer` (fila 4, BS con `KMV-CC-26-627`, la de la prueba visual).
- Piloto con `read_pilot` (sólo GET): Proyectos 14, Tareas 7, Records 6 y Revisiones 2 filas con ID; todas con Stable ID igual al visible, ninguna pendiente ni distinta.
- Sin acceso a PostgreSQL desde este equipo: no se consultaron asignaciones ni auditoría. Sin escrituras en Smartsheet.

# 2026-11-10 10:00 -05:00 ID Manager sobre Presentable (PEN-24)

- 315 pruebas backend aprobadas (nuevas: `test_id_presentable.py`, 3 casos; catálogo con hija repetida y sin columna de empresa); Ruff y formato correctos.
- Lectura real de Presentable (sólo GET): 4 madres y 3 hijas; las 3 hijas ya llevan el ID de su madre (`child_inherited`). DRY_RUN: 3 `conflict` (`KMV-BS-26-460`, `KMV-BS-26-461`, `KMV-CC-26-719` ya registrados para filas de las hojas anteriores) y 1 `register_existing` (`KMV-CC-26-718`). Automatizaciones de la hoja: 4, todas desactivadas.
- Sin escrituras en Smartsheet ni en PostgreSQL; el reinicio a 001 queda preparado.

# 2026-11-10 10:07 -05:00 Reinicio a 001 en Presentable (PEN-24)

- El usuario ejecutó `servicios/ids/reiniciar_registro.py --confirmar`: antes 34 asignaciones, 15 secuencias y 49 eventos; después 0, 0 y 0; registro inicializado; respaldo `~/galp_backups/galp_antes_reinicio_20261110_100532.dump`.
- Escrituras autorizadas en Pruebas: 7 Stable IDs de Presentable vaciados (versión 269 a 270, ninguno con valor después); 21 filas quitadas de la hoja catálogo (queda vacía); columna `Control Linked Tracking` agregada al final de Presentable con fórmula.
- DRY_RUN real posterior: 4 madres `needs_reservation` con propuesta igual a la fórmula (`KMV-BS-26-001`, `KMV-BS-26-002`, `KMV-CC-26-001`, `KMV-CC-26-002`) y 3 hijas `pending_parent`. Control: las 7 filas `LEGACY: NOT LOADED`.

# 2026-11-10 10:14 -05:00 Ejemplo de Presentable asignado desde 001 (PEN-24)

- Backend encendido por el usuario. Verificación de espera: DRY_RUN con 4 `already_stable` y 3 `child_inherited`; sincronización del catálogo `add` 4.
- Lectura independiente: madres `KMV-BS-26-001`, `KMV-BS-26-002`, `KMV-CC-26-001`, `KMV-CC-26-002`; hijas de las filas 1, 4 y 6 con el ID de su madre; visible igual a estable en las 7 filas. PostgreSQL: 4 asignaciones confirmadas, auditoría 4 `reservado` y 4 `confirmado`. Hoja catálogo: los 4 proyectos como `Actual`.
- Linked Tracking de Presentable conserva 21 opciones antiguas: no está vinculado al catálogo (SPEC-B16 LB-18).

# 2026-11-10 10:20 -05:00 Desplegable de Presentable vinculado (SPEC-B16, PEN-24)

- GET de columna: Linked Tracking (`6316483826978692`) PICKLIST con opciones `KMV-BS-26-001`, `KMV-BS-26-002`, `KMV-CC-26-001`, `KMV-CC-26-002`; `validation` false; descripción actualizada por el usuario.
- Celdas conservadas (296, 461, 638, 627); `Control Linked Tracking` = `LEGACY: NOT LOADED` en las 7 filas. La regla roja no es visible por API.

# 2026-11-10 10:52 -05:00 Flujo madre/hija real en Presentable (PEN-24)

- Filas de prueba creadas por API en Presentable (Pruebas): madre `PRUEBA - flujo madre/hija` (BS, 2026-11-10), hija creada ya indentada y `PRUEBA - fila suelta` sin Customer ni fecha.
- Madre: fórmula `KMV-BS-26-003` al crearla; Stable ID a los 61 s. Hija: muestra el ID de la madre al crearla; Stable ID igual a los 136 s. Fila suelta: sin número tras un ciclo completo; indentada a los 206 s, muestra el ID de la madre al instante y lo fija a los 270 s.
- Desplegable con `KMV-BS-26-003` agrupado con BS. DRY_RUN: 5 `already_stable`, 5 `child_inherited`; sin conflictos. PostgreSQL: 5 asignaciones (BS 001 a 003, CC 001 y 002).

# 2026-11-10 11:38 -05:00 Renumeración de madres copiadas (PEN-24)

- 317 pruebas backend aprobadas (nuevas: copia de madre con siguiente número, cliente cambiado y reintento con la misma reserva); Ruff y formato correctos.
- DRY_RUN real de Presentable: 6 `already_stable` y 11 `child_inherited`; ninguna fila detectada como copia. El servidor del usuario recargó el código a las 11:36:43.

# 2026-11-10 12:26 -05:00 Copia en vivo y reacción rápida del procesador (PEN-24)

- Prueba del usuario: pegó una copia de la madre `KMV-BS-26-003` (fila 21); el procesador le asignó `KMV-BS-26-004` unos 40 s después; la original y sus hijas conservaron `003`.
- Sondeo de versión cada 5 s implementado: 319 pruebas backend aprobadas; Ruff y formato correctos. El servidor del usuario recargó el código y `/api/ids/status` informa `processor_poll_seconds` 5.

# 2026-11-10 12:47 -05:00 Reportes de Presentable (PEN-42)

- Reportes creados en `Pruebas/Producto` (ids 8203968674221956, 3413810976345988, 8762864178515844, 8910360334782340). Lectura posterior: Permitting por persona 8 filas en 4 grupos; Invoices 5 filas (PM APPROVED); All Records Request 10 filas; MOT y Paquetes 0 filas porque hoy ninguna fila tiene a Carlos Carrillo ni a German Quiñe.
- Columna `Invoice Status` agregada al final de Presentable; valores actuales NOT INVOICED y PM APPROVED.

# 2026-11-12 13:30 -05:00 Conversaciones copiadas a Obs (PEN-46, SPEC-B17)

- 335 pruebas backend aprobadas (16 nuevas en `test_obs_rules.py` y `test_obs_sync.py`); Ruff y formato correctos.
- Vista previa real sin escrituras (sólo GET): 106 comentarios de filas en 49 filas, 7 vigentes; resultado en formato `11.12 - texto // texto`, con el texto previo de Obs conservado debajo y sin superar 4 000 caracteres.

# 2026-11-12 14:41 -05:00 Prueba real de Obs (PEN-46, SPEC-B17)

- Migración 004 aplicada por el usuario (con respaldo previo del script); backend reiniciado por el usuario con `APP_OBS_SYNC_ENABLED=true`.
- `/api/ids/status` (modo assign): primera pasada `last_obs_sync` = 7 filas, 61 comentarios, 0 archivados, 0 en espera, 0 errores; pasada siguiente (19:40:40 UTC) 0 filas, sin escrituras.
- PostgreSQL `obs_comentario`: 61 comentarios de 7 filas, registrados entre 14:39:13 y 14:39:29.
- Lectura de PROJECT KMV (sólo GET): las 7 filas vigentes con comentarios tienen `Obs` con la línea `11.12 - texto // texto` arriba y el texto anterior debajo (por ejemplo `10.08 - Awaiting confirmation...`, `** Renewal`, `Related to ...`); la más larga tiene 167 caracteres.

# 2026-11-12 15:02 -05:00 Títulos `**` en Obs (PEN-46, SPEC-B17 OB-16)

- 337 pruebas backend aprobadas (2 nuevas en `test_obs_rules.py`: secciones con títulos de chat y títulos escritos a mano); Ruff y formato correctos.
- El backend del usuario (con `--reload`) recargó el cambio: `/api/ids/status` con el procesador activo, ciclo 20:01:04 UTC sin errores y `last_obs_sync` sin filas pendientes.
- Prueba real con un chat `**` (2026-11-12 15:20, lectura por API): la fila quedó con `** Titulo nueva seccion`, debajo `11.12 - nueva seccion`, una línea en blanco y la sección anterior con su texto intacto; se ve igual en la Dynamic View KMV - CUSTOMERS.

# 2026-11-12 17:50 -05:00 Cambio de cliente y familia coherente (PEN-47, SPEC-ID01 ID-44 a ID-48)

- 342 pruebas backend aprobadas (5 nuevas en `test_id_customer_change.py`; las 66 de IDs existentes sin cambios con el interruptor apagado); Ruff y formato correctos.
- Fórmula de `Tracking Project` en PROJECT KMV cambiada por API a `Pending ID` (ID-48); relectura: fórmula aplicada y los 12 valores sin cambios.
- Prueba real (2026-11-12 17:58): migración 005 aplicada y backend reiniciado por el usuario; dos hijas de otro cliente pasaron a primer nivel con `KMV-CC-26-004` y `KMV-HC-26-001`, nota `#internal` en cada una, auditoría `reservado` y `confirmado`; ciclo siguiente sin acciones (6 `already_stable`, 6 `child_inherited`). Cambio de cliente de una madre (2026-11-12 18:04): `KMV-BS-26-008` retirado y `KMV-LP-26-001` confirmado; sus dos hijas con cliente LP y ese ID. Notas `#internal` quitadas del código y borradas de la hoja (3); 342 pruebas aprobadas tras el cambio.

# 2026-11-13 09:59 -05:00 Hoja maestra configurable y traslado a PROJECT KMV 1.0.0 (PEN-48, SPEC-ID01 ID-50)

- 346 pruebas backend aprobadas (4 nuevas en `test_id_rehome.py`); Ruff y formato correctos.
- Traslado real: simulación y `--confirmar` con 8 madres, 68 comentarios y 7 asignaciones que siguen en la hoja anterior; base: 8 asignaciones en la copia y 7 en la anterior; simulación del procesador sobre la copia sin pendientes (8 `already_stable`, 6 `child_inherited`) y Obs sin pendientes.

# 2026-11-13 10:10 -05:00 Hoja hija de Records (PEN-49, SPEC-B18)

- 352 pruebas backend aprobadas (6 nuevas en `test_records_sync.py`); Ruff y formato correctos.
- Hoja `Records Requests` creada por API en Pruebas y releída: 23 columnas, contexto bloqueado, `Master Row` oculta, fórmulas y 3 referencias OK; casilla `Records Needed` en la maestra.
- Vista previa real sin escrituras: 14 filas, ninguna marcada, nada que crear. Prueba real pendiente del reinicio.
- Prueba real (2026-11-13 10:20): 9 filas marcadas en la maestra y 9 en Records, sin duplicados ni faltantes, contexto igual; valores iniciales copiados donde la hoja hija no se editó después.
