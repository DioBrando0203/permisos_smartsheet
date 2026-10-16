# Panel de permisos de Smartsheet

Panel interno para ver quién tiene acceso a las hojas de Smartsheet de la cuenta y administrar esos permisos sin entrar hoja por hoja en Smartsheet:

- Lista de hojas con su cantidad de personas con acceso y búsqueda por nombre.
- Detalle de una hoja: cada usuario o grupo, su nivel de acceso y si el permiso es propio de la hoja o heredado del workspace.
- Dar acceso a una o varias personas (correo o grupo) con un nivel, con o sin correo de aviso.
- Cambiar el nivel de acceso de una persona y quitarle el acceso, con confirmación.
- Vista por usuario: en qué hojas tiene acceso una persona y con qué nivel.
- Directorio: contactos de la libreta de Smartsheet, personas con acceso y usuarios de la organización en una sola lista, para dar acceso a cualquiera de ellos.

El token de Smartsheet vive sólo en `backend/.env`; el navegador nunca lo recibe. No hay base de datos: Smartsheet es la única fuente de verdad y el backend sólo guarda en memoria una caché corta.

Estado: documentación inicial lista (2026-10-12). Backend en desarrollo; el frontend empieza cuando el backend esté probado. Plan y pendientes: [requerimientos](backend/docs/REQUERIMIENTOS.md).

## Estructura

```text
backend/    API FastAPI que habla con Smartsheet (token, reglas de permisos, caché)
frontend/   React + TypeScript + Vite con Fluent 2 (se construye después del backend)
AGENTS.md   guía breve para retomar el proyecto (personas o IA)
```

## Puertos

- Backend: `http://127.0.0.1:8710` (API en `/api`, OpenAPI en `/docs`). Si el 8710 está ocupado, `python run.py` usa uno libre al azar y lo muestra al arrancar.
- Frontend en desarrollo: `http://127.0.0.1:5710`.
- Elegidos para no chocar con otros proyectos locales (8000 y 5173).

## Configuración

1. Copiar `backend/.env.example` a `backend/.env` y completar `SMARTSHEET_ACCESS_TOKEN`.
2. Si la cuenta es de Europa o Australia, cambiar `SMARTSHEET_BASE_URL`.
3. `APP_READ_ONLY=true` (por defecto) bloquea dar, cambiar y quitar accesos: el panel sólo consulta. Poner `false` cuando se quiera escribir en Smartsheet.

## Arranque

Guía completa para Windows y Linux: [LEVANTAMIENTO.md](LEVANTAMIENTO.md).

Primera vez (Python 3.11+):

```bash
cd backend
python3 -m venv .venv
.venv/bin/python -m pip install -c requirements.lock -e '.[dev]'
cd ..
```

Cada vez:

```bash
cd backend
source .venv/bin/activate      # Windows: .venv\Scripts\activate
python run.py
```

Muestra la dirección, por ejemplo `Backend: http://127.0.0.1:8710/docs`. Recarga sola al cambiar el código; si se cambia `backend/.env`, detener con Ctrl+C y volver a iniciar.

## Verificación

```bash
cd backend
.venv/bin/python -m pytest
.venv/bin/python -m ruff check app tests
.venv/bin/python -m ruff format --check app tests
```

Documentación de continuidad: [guía de agentes](AGENTS.md), [backend](backend/docs/README.md) y [frontend](frontend/docs/README.md).
