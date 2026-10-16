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
