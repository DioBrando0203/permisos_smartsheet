# Levantamiento del backend

El backend se levanta siempre desde la carpeta `backend`. Usa el puerto 8710; si está ocupado, elige uno libre al azar y lo muestra al arrancar.

## Requisitos

- Python 3.11 o superior.
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
py -m venv .venv
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

## Problemas comunes

- `ModuleNotFoundError: No module named 'uvicorn'`: el entorno no está activado o falta la instalación de la primera vez.
- `"smartsheet": "missing_token"` en `/api/health`: falta `SMARTSHEET_ACCESS_TOKEN` en `backend/.env`.
- Error `SMARTSHEET_AUTH`: el token es inválido o fue revocado; generar uno nuevo en Smartsheet (Personal Settings, API Access).
