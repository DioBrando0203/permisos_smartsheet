# Plan de calidad (backend)

Reglas en `reglas_calidad/REGLAS.md`. Última ejecución en `RESULTADOS.md`.

## Mapa de pruebas

- `tests/conftest.py`: `make_settings` (token ficticio, sin esperas entre reintentos, escritura habilitada), `smartsheet` (respx con rutas por defecto; una solicitud no simulada falla), `make_client` y `client` (`httpx.AsyncClient` con `ASGITransport`), `writes` (escrituras que llegaron a Smartsheet simulado).
- `tests/factories.py`: JSON sintético de Smartsheet con correos `@example.com`.
- `test_client.py`: cabecera con token y logs sin token, 429 con reintentos, 500 reintentado en lectura y no en escritura, `lastKey`, 401 traducido, token ausente.
- `test_shares.py`: SPEC-B02 completa: bloqueos, solo lectura, propietario, heredado, duplicados, omitidos, sin correo por defecto, cuerpos y query enviados, no-op, invalidación de caché, ids inválidos.
- `test_people.py`: SPEC-B03 y búsqueda de SPEC-B01.
- `test_permissions.py`: reglas para todos los niveles y scopes, orden, duplicados, caché (vencimiento, single flight, invalidación).
- `test_security.py`: Origin, Host, salud sin llamadas, token secreto, solo lectura por defecto, listas del entorno.

## Comandos

Desde `backend/`:

- `.venv/bin/python -m pytest` (Windows: `.venv/Scripts/python.exe`).
- `.venv/bin/python -m ruff check app tests`.
- `.venv/bin/python -m ruff format --check app tests`.

## Verificación manual con la cuenta real

- Lecturas: levantar con `--env-file .env`, abrir `/docs` y ejecutar `GET /api/me`, `/api/sheets`, `/api/sheets/{id}/shares`, `/api/users`. Anotar cantidades y tiempos en RESULTADOS, sin nombres ni correos.
- Escrituras: sólo en la hoja y con el correo de prueba que designe el usuario (PEN-07). Orden: crear, cambiar, quitar; confirmar en Smartsheet que quedó como al inicio.

## Cuándo ampliar

- Endpoint nuevo de Smartsheet: éxito, 404, 429 y 5xx.
- Regla nueva de permisos: todos los niveles y scopes (QB-05).
- Cambio de contrato: actualizar `estilos/API.md` y, si existe, los tipos del frontend.
