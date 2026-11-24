# SPEC-B22 Procesador en un servidor (Railway u otro)

Estado: preparado el 2026-11-24 (PEN-56, pedido del usuario: "de la forma más escalable considerando que igual haremos cambios"), con pruebas simuladas y un ensayo de la mudanza con los datos reales en una base local descartable. Sin desplegar. Antes de subir el token, el usuario debe decidir qué cuenta de Smartsheet usa el servidor (DP-11). Guía paso a paso: `../DESPLIEGUE_RAILWAY.md`.

## Contexto

- El procesador (ID Manager, hojas de equipo, `Obs`, metraje) y su PostgreSQL sólo corren si el equipo Linux está encendido (B-16). Apagado, los IDs quedan en `Pending ID` y nada se copia (mapa MP-79). El usuario contrató Railway, plan Hobby: $5 al mes con $5 de consumo incluido.
- Railway retira su configuración en archivo (`railway.json`) el 2026-12-01: nada de este diseño depende de ella.

## Reglas

- DP-01: una sola imagen Docker (`Dockerfile` en la raíz del repo, porque lleva `backend/app` y `servicios/ids/sql`) define cómo se construye y arranca. Sirve en Railway o en cualquier servidor con Docker. Los ajustes propios de Railway (salud, réplicas, espera de CI) se hacen en su panel o con su CLI, según la guía.
- DP-02: los secretos (token de Smartsheet, `IDS_ADMIN_TOKEN`, URL de la base) sólo existen como variables del servidor. `.dockerignore` deja fuera todo `.env`, `.venv`, docs y pruebas; la imagen no lleva ningún secreto.
- DP-03: `IDS_DATABASE_URL` (secreta, como el token: nunca en `repr`, logs ni respuestas) elige la base. Vacía: la local del equipo Linux con `galp_ids` y su pgpass, como hasta ahora (`services/ids/cli.py`, `database_dsn`).
- DP-04: al arrancar en un servidor (`python -m app.serve`), primero las migraciones (`services/ids/migrations.py`) y después Uvicorn.
  - Son los mismos archivos `servicios/ids/sql/NNN_nombre.sql` que en el equipo Linux se aplican a mano. Van en orden, cada uno una sola vez, y su registro en `migracion_esquema` entra en la misma transacción: una migración que falla no deja nada a medias.
  - Un bloqueo propio evita que dos arranques migren a la vez.
  - Una base con migraciones aplicadas a mano y sin registro (la de B-16 restaurada con `pg_dump`) no se toca hasta registrarla una vez con `--baseline NNN`. La mudanza de DP-08 no lo necesita.
  - Si las migraciones fallan, el servicio no arranca: Railway mantiene el despliegue anterior.
- DP-05: nunca dos procesadores a la vez. Un proceso y un worker; una réplica. El bloqueo global de PostgreSQL ya lo garantizaba, pero un monitor que no lo conseguía se rendía para siempre. Ahora reintenta cada 30 s, y lo mismo si PostgreSQL no responde (antes quedaba en `database_unavailable` hasta reiniciar). En un despliegue, la versión nueva arranca antes de que se apague la anterior: espera a que suelte el bloqueo y sigue sola.
- DP-06: sin dominio público. El procesador no necesita recibir visitas; dentro del contenedor escucha en `0.0.0.0` y en el puerto `PORT` que da el servidor (`APP_HOST` lo cambia). Quién llega lo deciden Railway (red privada) y `APP_ALLOWED_HOSTS`. La API del ID Manager sigue exigiendo `IDS_ADMIN_TOKEN`.
- DP-07: chequeo de salud en `/api/health`, que no llama a Smartsheet. Railway lo hace sólo al desplegar y con el nombre `healthcheck.railway.app`, que debe estar en `APP_ALLOWED_HOSTS` (la imagen lo trae por defecto; si el servidor define la variable, debe incluirlo).
- DP-08: mudanza de la base (`services/ids/transfer.py`), desde el equipo Linux con el backend apagado:
  - Lee el origen sin modificarlo; basta `galp_ids`, sin `sudo`. `pg_dump` exigiría `sudo`: `galp_ids` no puede leer la secuencia de la auditoría.
  - Migra el destino y exige que esté vacío.
  - Toma el bloqueo del procesador en las dos bases.
  - Copia las seis tablas con `COPY` en una sola transacción y deja la secuencia de la auditoría después del último valor.
  - Compara filas y huella del contenido de cada tabla en las dos bases: si algo no coincide, el destino queda vacío.
  - Una tabla nueva del origen que no esté en la lista detiene la copia.
- DP-09: cada push a `main` y cada pull request corren en GitHub Actions `ruff check`, `ruff format --check` y `pytest` con PostgreSQL 18 (`.github/workflows/backend.yml`). Con "Wait for CI" en Railway, un commit sólo se despliega si eso pasa.
- DP-10: después de mudar, el equipo Linux no vuelve a numerar con su base local. Su `.env` lleva también `IDS_DATABASE_URL` del servidor: si alguien lo enciende, espera el bloqueo (DP-05) y sirve de respaldo si el servidor se cae. La otra opción es `IDS_MONITOR_ENABLED=false`. La base local queda como copia, sin usar.
- DP-11 (decisión pendiente del usuario): el token del servidor. Hoy es el de un administrador de la cuenta y sólo vive en `backend/.env`. Subirlo a Railway lo deja en la nube de un tercero; lo más seguro es el token de una cuenta que sólo vea el workspace `Pruebas` (el servicio sólo escribe allí). Hasta decidirlo no se sube ningún token.

## Costo y carga

- DP-20: un proceso de Python y PostgreSQL chicos, siempre encendidos. Estimado (no medido): $3 a $6 al mes de memoria y CPU, cerca de los $5 incluidos. La guía pide un límite de gasto en Railway.
- DP-21: el consumo de la API de Smartsheet no cambia: es el mismo servicio (SPEC-B21).

## Criterios de aceptación

- CA-01: con `IDS_DATABASE_URL` se usa esa base; sin ella, o vacía, la local; la URL no aparece en `repr` de la configuración. Prueba: `test_deploy.py`.
- CA-02: sin `IDS_DATABASE_URL` ni el arranque de servidor ni las migraciones corren; escucha en `PORT` (8710 si falta). Prueba: `test_deploy.py`.
- CA-03: una base vacía recibe todas las migraciones una vez; una segunda pasada no aplica nada. Prueba: `test_deploy.py`.
- CA-04: una base con migraciones a mano exige `--baseline`; después, una migración nueva se aplica una sola vez. Prueba: `test_deploy.py`.
- CA-05: una migración que falla no deja tablas ni registro a medias. Prueba: `test_deploy.py`.
- CA-06: la mudanza copia todo, deja la auditoría numerando después de lo copiado y nunca escribe sobre una base con datos ni con un procesador activo. Prueba: `test_deploy.py`.
- CA-07: el monitor espera mientras otra instancia tiene el bloqueo, toma el relevo sin reiniciarse y se reconecta cuando vuelve PostgreSQL. Prueba: `test_idsmart.py`.
- CA-08: ninguna prueba depende del `.env` local (corridas sin él, como en GitHub Actions).

## Ensayo real (2026-11-24, sólo lectura del origen)

- Base del equipo Linux (PostgreSQL 18.6, backend apagado) copiada a un PostgreSQL local descartable con `transfer.py`: `secuencia_id` 6, `estado_inicializacion_id` 1, `asignacion_id` 24, `auditoria_id` 57, `obs_comentario` 142, `id_retirado` 2, con huellas iguales; migraciones 001 a 005 registradas. La base de ensayo se borró.
