# Levantamiento del backend

El backend se levanta siempre desde la carpeta `backend`. Usa el puerto 8710; si está ocupado, elige uno libre al azar y lo muestra al arrancar.

## Requisitos

- Python 3.14. Con 3.11 a 3.13 el backend no arranca (B-12 en `backend/docs/bloqueos/BLOQUEOS.md`).
- Archivo `backend/.env` con el token de Smartsheet (copiar de `backend/.env.example` y completar `SMARTSHEET_ACCESS_TOKEN`).

## Linux

Primera vez:

```bash
cd permisos_smartsheet/backend
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -c requirements.lock -e '.[dev]'
```

Cada vez:

```bash
cd permisos_smartsheet/backend
source .venv/bin/activate
python run.py
```

## Windows (PowerShell)

Primera vez:

```powershell
cd permisos_smartsheet\backend
py -3.14 -m venv .venv
.venv\Scripts\activate
python -m pip install -c requirements.lock -e ".[dev]"
```

Cada vez:

```powershell
cd permisos_smartsheet\backend
.venv\Scripts\activate
python run.py
```

Si PowerShell no deja activar el entorno ("la ejecución de scripts está deshabilitada"), ejecutar una vez `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`, o usar directamente `.venv\Scripts\python.exe run.py`.

## Al arrancar

- Muestra la dirección, por ejemplo `Backend: http://127.0.0.1:8710/docs`.
- Swagger para probar: `http://127.0.0.1:8710/docs` (o el puerto que indique).
- Comprobación rápida: `http://127.0.0.1:8710/api/health` debe responder `"smartsheet": "configured"`.
- Recarga sola al cambiar el código. Si se cambia `backend/.env`, detener con Ctrl+C y volver a ejecutar `python run.py`.
- Modo solo lectura activo por defecto (`APP_READ_ONLY=true` en `backend/.env`): ninguna escritura llega a Smartsheet.

## Modo de prueba con el Smartsheet falso

Para ver o probar el panel con datos inventados, sin tocar la cuenta real (y con escrituras habilitadas sólo contra el falso). Linux, dos terminales desde `backend` con el entorno activado:

```bash
# Terminal 1: Smartsheet falso en el puerto 8791
python -m tests.fake_smartsheet --port 8791

# Terminal 2: backend apuntando al falso (estas variables ganan al .env)
SMARTSHEET_ACCESS_TOKEN=fake-token SMARTSHEET_BASE_URL=http://127.0.0.1:8791/2.0 \
APP_READ_ONLY=false APP_DESIGNER_CATALOG_SHEET=3333333333333333 python run.py
```

En Windows (PowerShell), en la terminal 2: `$env:SMARTSHEET_ACCESS_TOKEN="fake-token"; $env:SMARTSHEET_BASE_URL="http://127.0.0.1:8791/2.0"; $env:APP_READ_ONLY="false"; $env:APP_DESIGNER_CATALOG_SHEET="3333333333333333"; python run.py`.

`/api/me` debe mostrar "Cuenta de prueba". Escrituras recibidas: `http://127.0.0.1:8791/_fake/writes`; volver al estado inicial: `POST http://127.0.0.1:8791/_fake/reset`.

## Pruebas E2E del frontend

Desde `frontend`, con el entorno del backend ya creado y `npx playwright install chromium` hecho una vez: `npm run test:e2e`. Playwright levanta solo el Smartsheet falso (8791), el GIS falso (8792), el backend de prueba (8793, `tests.e2e_backend`: solo lectura y sin leer el token de `backend/.env`) y Vite (5791), y los detiene al terminar. Si alguno de esos puertos está ocupado, falla en vez de reutilizar un servidor que podría hablar con la cuenta real.

## Problemas comunes

- `ModuleNotFoundError: No module named 'uvicorn'`: el entorno no está activado o falta la instalación de la primera vez.
- `"smartsheet": "missing_token"` en `/api/health`: falta `SMARTSHEET_ACCESS_TOKEN` en `backend/.env`.
- Error `SMARTSHEET_AUTH`: el token es inválido o fue revocado; generar uno nuevo en Smartsheet (Personal Settings, API Access).
