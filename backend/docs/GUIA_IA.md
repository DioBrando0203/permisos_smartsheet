# Guía operativa para agentes IA (backend)

Protocolo obligatorio para cualquier IA que modifique `backend/`. Si contradice una instrucción explícita del usuario, gana el usuario y se registra en la bitácora.

## Contexto mínimo

- Servicio FastAPI que por defecto sólo escucha en 127.0.0.1; el acceso desde la red es opcional y explícito (ADR-B08).
- Intermediario entre el panel y la API 2.0 de Smartsheet. Smartsheet es la única fuente de verdad (ADR-B02).
- El token es de un administrador de la cuenta: toda escritura es real, inmediata y visible para las personas afectadas.
- Sin base de datos. Caché en memoria con vencimiento corto que se invalida al escribir (ADR-B06).
- El token sólo se lee de `SMARTSHEET_ACCESS_TOKEN`. Nunca se devuelve, se registra ni se escribe en docs o pruebas.

## Flujo de trabajo (SDD)

1. Entender: leer la spec y el código real del paquete afectado.
2. Especificar: actualizar o crear la spec con criterios de aceptación verificables (CA-xx).
3. Diseñar: ubicar el cambio según "Dónde va cada cosa"; elegir patrón en `patrones/PATRONES.md`.
4. Implementar: respetar PY-xx y SM-xx; funciones cortas; sin duplicar lógica existente.
5. Probar: prueba con respuestas simuladas de Smartsheet (`respx`) que falle antes del cambio y pase después.
6. Verificar: comandos de la sección Verificación; si cambió una lectura, comprobarla también contra la cuenta real (sólo GET).
7. Registrar: resultados, bitácora y, si aplica, bloqueos y ADR.

## Definición de terminado

- `pytest`, `ruff check` y `ruff format --check` pasan.
- Ningún módulo nuevo o modificado supera 300 líneas ni una función 60 (PY-01, PY-02).
- Spec, `ARQUITECTURA.md` y `estilos/API.md` reflejan el contrato real.
- Si cambió el contrato y el frontend existe: tipos y normalización del frontend actualizados.
- Bitácora con hora America/Lima y evidencia real.

## Prohibiciones

- No exponer el token: ni en respuestas, ni en logs, ni en mensajes de error, ni en `repr` de la configuración (SM-01).
- No llamar a Smartsheet desde las pruebas automáticas. Todo `httpx` se simula con `respx` (QB-02).
- No desactivar `APP_READ_ONLY` sin que el usuario lo pida (ADR-B11).
- No probar escrituras (POST, PATCH, DELETE) contra hojas reales salvo en la hoja de prueba que el usuario designe y anotando en la bitácora qué se hizo y cómo se revirtió.
- No asignar ni modificar el nivel `OWNER`, ni borrar el permiso del propietario (ADR-B04).
- No modificar desde una hoja un permiso con `scope=WORKSPACE`; se administra en el workspace (ADR-B05).
- No enviar correos de aviso de Smartsheet salvo que la solicitud lo pida (`send_email=true`); por defecto `false` (SM-07).
- No devolver el JSON crudo de Smartsheet: siempre el contrato propio de `models/` (PY-14).
- No guardar correos, nombres ni permisos reales en disco, logs, fixtures o docs.
- No subir límites de concurrencia ni quitar reintentos para "ir más rápido" (SM-05).

## Dónde va cada cosa

- Ruta HTTP nueva o parámetro: `app/api/routes/`. Sólo coordina: valida, llama al servicio, responde.
- Dependencias de FastAPI (cliente, caché, servicios): `app/api/deps.py`.
- Llamadas HTTP a Smartsheet, autenticación, reintentos y paginación: `app/services/smartsheet/client.py`; traducción de errores en `errors.py`.
- Traducir JSON de Smartsheet al modelo interno: `app/services/smartsheet/mappers.py`.
- Operaciones de negocio sobre hojas, permisos y personas: `app/services/sheets.py`, `shares.py`, `people.py`; agregación pura del directorio en `directory.py`.
- Reglas puras de permisos (orden de niveles, qué se puede editar, validación de altas): `app/services/permissions/`.
- Caché en memoria: `app/services/cache.py`.
- Contrato JSON: `app/models/`.
- Configuración y límites: `app/core/config.py`.
- Errores con código seguro: `app/core/errors.py`.

## Cómo añadir una operación de Smartsheet

1. Documentar el endpoint de Smartsheet y su respuesta real en la spec (GET verificado contra la cuenta; escrituras, según la documentación oficial hasta verificarlas).
2. Añadir el método en `client.py` usando `_request` (nunca `httpx` directo en otro módulo).
3. Mapear la respuesta en `mappers.py` a un dataclass interno.
4. Exponerlo desde el servicio de dominio y, si aplica, una ruta.
5. Pruebas con `respx`: éxito, 404, 429 con reintento y error del servidor.

## Verificación

Desde `backend/` (Windows: `.venv/Scripts/python.exe`; Linux: `.venv/bin/python`):

- `python -m pytest`
- `python -m ruff check app tests`
- `python -m ruff format --check app tests`
- Prueba manual de lectura: `uvicorn app.main:app --env-file .env` y `/docs`.
