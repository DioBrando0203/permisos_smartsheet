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
