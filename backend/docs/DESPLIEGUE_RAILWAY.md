# Procesador en Railway: guía y estado

Guía para llevar el procesador (ID Manager, hojas de equipo, `Obs`, metraje) y su PostgreSQL del equipo Linux a Railway, y para mantenerlo allí. Reglas y criterios: `specs/SPEC-B22-despliegue-servidor.md` (DP-xx). Decisión: `decisiones/ADR.md` ADR-B19. Pendiente: `REQUERIMIENTOS.md` PEN-56.

## Estado (2026-11-24 18:01)

- RW-01: proyecto `KMV` en Railway, entorno `production`, con dos servicios:
  - `permisos_smartsheet`: conectado al repo de GitHub, rama `main`. Su primer despliegue (commit `c237c26`, sin `Dockerfile`) falló sin llegar a correr.
  - `Postgres`: base nueva, sólo en la red privada de Railway.
- RW-02: hecho con la CLI de Railway, desde el equipo Linux:
  - Variables de `permisos_smartsheet` (`servicios/despliegue/variables_railway.py`), 36 en total: los 34 ajustes de `backend/.env` que no son secretos ni propios del equipo Linux, sin el token de Smartsheet y con el procesador apagado (`IDS_MONITOR_ENABLED=false`).
  - La base va por referencia: `IDS_DATABASE_URL=${{Postgres.DATABASE_URL}}`.
  - `APP_ALLOWED_HOSTS` incluye `healthcheck.railway.app` y el dominio privado.
  - `IDS_ADMIN_TOKEN` nuevo, generado para el servidor.
  - Ajustes del servicio por la API de Railway: `Dockerfile`, chequeo de salud `/api/health` (120 s), reinicio siempre, una réplica, sin dormir, y redespliegue sólo si cambian `Dockerfile`, `.dockerignore`, `backend/app/**`, `backend/requirements.lock` o `servicios/ids/sql/**` (los commits de docs no redespliegan).
- RW-03: hecho después, con las decisiones del usuario (2026-11-24):
  - Registro de IDs copiado y verificado en Railway (17:48): `secuencia_id` 6, `estado_inicializacion_id` 1, `asignacion_id` 24, `auditoria_id` 57, `obs_comentario` 142, `id_retirado` 2. Se usó un acceso público temporal (RW-21), cerrado al terminar.
  - En el equipo Linux, `IDS_MONITOR_ENABLED=false` en `backend/.env`: su base local queda como copia y no vuelve a numerar (RW-22).
  - Token de administrador (DP-11) y `IDS_MONITOR_ENABLED=true` en las variables del servidor.
  - Aviso de gasto a $8 por correo (soft); sin tope.
- RW-04: en marcha desde el push del usuario (2026-11-24 17:53):
  - Despliegue del commit `74efda8` en `SUCCESS`.
  - Logs: "Migraciones aplicadas: ninguna pendiente", Uvicorn en el puerto de Railway y chequeo de salud con 200.
  - El procesador ya lee la maestra, las hojas de equipo y las conversaciones (modo asignación). Sin avisos ni errores, y sin escrituras porque no había nada pendiente.
  - A los 3 minutos pasó a la consulta lenta, cada 30 s.
- RW-05: consumo medido (15 min, sin trabajo): servicio 66 MB y base 110 MB de memoria, menos de 0,01 vCPU cada uno. Da unos $2 al mes, dentro de los $5 incluidos.
- RW-06: prueba del usuario (2026-11-24, 18:15): un proyecto `KMV-P` (fila 16) y un permiso `KMV-Permit` debajo (fila 17). Entre las 18:16 y las 18:19, el procesador de Railway:
  - Numeró el proyecto `KMV-26-0007`, el siguiente a los copiados, sin repetir. El permiso quedó debajo con el mismo ID.
  - Sumó el ID a las listas `Parent Project` y `Linked Tracking`.
  - Creó las dos filas en `Billing` y devolvió `Invoice Status` (`NOT INVOICED`).
  - Creó la fila de `Design Tickets`.
  - Sin avisos ni errores.
  - Sin filas en `Permits` ni en Records, como manda la regla: el permiso no tiene `Agency`. Una hija pasa a `Permits` con su tipo y su agencia (SPEC-B20), y un pedido de Records necesita la agencia, que es a quién se pide (RH-03). Con `Agency` llena, aparecen en el ciclo siguiente.
  - Observación: `DT Owner` quedó en el permiso, no en el proyecto (K2-23 lo pone en el proyecto). Por eso la fila de `Design Tickets` es del permiso. El servicio hoy crea esa fila para cualquier fila con `DT Owner`.
- RW-06b: lo que le faltó a la prueba del usuario:
  - `Agency` en el permiso (fila 17): sin ella no hay fila en `Permits` ni pedido de Records, aunque tenga `Records Needed` y `Records Owner`. La vista `PERMITS` la exige al crear (VK-18); la fila se llenó directo en la hoja.
  - `DT Owner` va en el proyecto (K2-23), no en el permiso.
- RW-08: proyecto de prueba permanente, pedido por el usuario para mantenerlo (2026-11-24, 18:26):
  - `KMV-26-0008`, `OT - SERVICE TEST - 100 TEST AVE`, cliente `OT-Others` (sin contactos en `Customer List`: la vista de clientes no lo muestra a nadie).
  - Filas 19 (proyecto, con `Prepare Packages` y `DT Owner`), 20 (`KMV-Permit`, `FDOT`, con Records pedido), 21 (`KMV-Line`, `Miami`) y 22 (`KMV-MOT`, `FDOT (MOT Permit)`).
  - Se crearon como lo haría la coordinación: el proyecto solo, y los trámites sueltos con `Parent Project`.
  - Resultado, todo desde Railway:
    - ID en 1 minuto, y los tres trámites debajo de su proyecto con sus datos heredados en menos de 1 minuto.
    - `Permits` 2, Records 1, `Billing` 4, `MOT & Packages` 2 (`MOT` y `Package`), `Design Tickets` 1.
    - Un comentario en la fila del permiso en `Permits` llegó al `Obs` de la fila 20 en unos 3 minutos: `11.24 - Application submitted to FDOT (service test).` (OB-17).
    - Logs sin avisos ni errores.
  - Avisos de las seis hojas apagados al momento de la prueba: no salieron correos.
- RW-07: falta, opcional:
  - "Wait for CI" en el panel (RW-41).
  - Ver el resultado de GitHub Actions en la pestaña Actions del repo. En el equipo Linux no está la CLI `gh`, así que no se comprobó desde aquí.
  - K2-99 decidido y hecho el 2026-11-24 (`Design Tickets` sólo para proyectos); rige con el despliegue de ese código.

## Cambios del día a día

- RW-10: un cambio de código llega a Railway con el push a `main`: GitHub Actions corre ruff y pytest (DP-09) y Railway construye la imagen y la despliega. Con "Wait for CI" encendido, espera a que las pruebas pasen.
- RW-11: una migración nueva es un archivo `servicios/ids/sql/NNN_nombre.sql` con el número siguiente. En Railway se aplica sola al desplegar (DP-04); en el equipo Linux, a mano con su script y respaldo, como siempre.
- RW-12: un interruptor nuevo en `backend/.env` (por ejemplo `APP_..._ENABLED`) se pasa a Railway con `backend/.venv/bin/python servicios/despliegue/variables_railway.py --monitor`. No toca el token ni el `IDS_ADMIN_TOKEN` del servidor. El script no redespliega: después, `railway service redeploy --service permisos_smartsheet` o el botón Deploy del panel, para que el servicio tome las variables.
- RW-13: ver qué pasa: `railway logs` (o el panel de Railway) muestra la consola del servicio. `GET /api/ids/status` y `/api/ids/logs` (SPEC-B21) se consultan desde la red privada o con `railway ssh`.
- RW-13b: cómo leer los logs (pregunta del usuario, 2026-11-24):
  - Cada línea `GET /sheets/<id>... -> 200` es una lectura correcta de Smartsheet.
  - Ids de las hojas: maestra `1979884168761220`, `Permits` `3435959686483844`, Records `3471473697312644`, `Billing` `4630718656499588`, `MOT & Packages` `2866571577085828`, `Design Tickets` `263146012102532`.
  - Sin trabajo se repite este patrón:
    - `/version` de la maestra cada 30 s: si cambió.
    - Cada minuto, un ciclo: lee la maestra (filas sin ID) y pregunta la versión de cada hoja de equipo; la que no cambió no se relee.
    - Cada 2 minutos, `/discussions` de la maestra y de `Permits`: comentarios nuevos para `Obs`.
  - Con trabajo aparecen `PUT` o `POST` (escrituras) y la consulta pasa a cada 5 s.
  - Avisos y errores salen como `WARNING` o `ERROR`.
  - Medido sin trabajo: 14 a 20 llamadas por minuto. El límite de Smartsheet es 300 y el freno propio, 250.
- RW-14: nunca más de una réplica ni más de un worker. Si en un despliegue conviven dos versiones, la nueva espera el bloqueo (DP-05).
- RW-15: la CLI de Railway en el equipo Linux (instalada el 2026-11-24, versión 5.75.0):
  - Se instala con `npm install -g @railway/cli@5.75.0`, sin `sudo`.
  - `railway login`: el usuario confirma en su navegador. La sesión queda guardada en el equipo; `railway logout` la cierra.
  - Desde la raíz del repo, `railway link --project KMV --environment production --service permisos_smartsheet`. Sólo guarda la asociación en la configuración de la CLI, nada en el repo.
  - Crear recursos que cuestan dinero (una base, un servicio) pide el visto bueno del usuario: el control de permisos bloqueó un segundo intento de crear la base, que además habría quedado duplicada.

## Mudanza de la base (RW-20)

- RW-20: desde `backend/` en el equipo Linux, con el backend apagado: `DESTINO_URL='<URL pública de la base de Railway>' .venv/bin/python -m app.services.ids.transfer`. Copia las seis tablas en una transacción y compara su contenido; si algo no coincide, el destino queda vacío (DP-08). Ensayado con los datos reales en una base local descartable (SPEC-B22).
- RW-21 (decisión del usuario): la base de Railway hoy sólo acepta conexiones de su red privada. Para la copia necesita una dirección pública (TCP proxy de Railway, con usuario y clave larga). Dos opciones:
  - Temporal: abrirla para la copia y cerrarla después. El equipo Linux queda con `IDS_MONITOR_ENABLED=false`.
  - Permanente: el `.env` del equipo Linux apunta a la misma base (DP-10). Si alguien enciende el backend allí, espera el bloqueo, y sirve de respaldo si Railway se cae.
- RW-22: justo después de la copia, el equipo Linux deja de usar su base local (DP-10): o apunta a la de Railway, o apaga su procesador. Si numerara con la local, se repetirían IDs.

## Encender el procesador (RW-30)

- RW-30: con el token decidido (DP-11): `backend/.venv/bin/python servicios/despliegue/variables_railway.py --monitor --con-token` y un redespliegue. El script manda el token por la entrada estándar, nunca en la línea de comandos ni en pantalla.
- RW-31: comprobar en los logs el primer ciclo sin errores, y en Smartsheet (Pruebas) que una fila nueva recibe su ID. Desde entonces el equipo Linux no procesa (DP-10).
- RW-32 (2026-11-25): el token del servidor es propio (DP-11). Para cambiarlo: generar uno nuevo en Smartsheet (Personal Settings, API Access), pegarlo en el panel de Railway (servicio `permisos_smartsheet`, Variables, `SMARTSHEET_ACCESS_TOKEN`) y aplicar el cambio con Deploy: el panel deja el cambio en espera ("Apply 1 change") hasta entonces. No usar `variables_railway.py --con-token`, que manda el de `backend/.env`. Después, revisar en los logs que las llamadas a Smartsheet respondan 200 y no 401.

## Costo y panel

- RW-40: plan Hobby: $5 al mes con $5 de consumo incluido; lo que pase de eso se cobra aparte. Estimado del servicio y la base: $3 a $6 al mes (DP-20). Conviene un límite en `Workspace > Usage`: el aviso (soft) no apaga nada; el tope (hard) apaga los servicios al llegar, y con ellos el procesador.
- RW-41: "Wait for CI" se enciende en el panel: en los `Settings` del servicio `permisos_smartsheet`, junto a la fuente de GitHub. Exige el workflow `.github/workflows/backend.yml`, que ya está en el repo.
- RW-42: la configuración en archivo de Railway (`railway.json`) se retira el 2026-12-01; por eso los ajustes viven en el servicio (RW-02) y en el `Dockerfile`.


## Paso a producción

- RW-60: decidido por el usuario (2026-11-24): mientras se prueba, todo queda como está. Al pasar a producción se borra toda la base y se empieza limpio con la maestra de producción. Orden y lista previa: `KMV_2.0.md` K2-102.

## Preguntas del usuario (2026-11-24)

- RW-50: "Pagué $5 de Railway, ¿qué me recomiendas hacer?"
  - Llevar allí el procesador y su base, para que corra sin depender del equipo Linux (el punto débil, K2-91).
  - Antes, dos decisiones suyas: qué token usa y dejar de correr sólo en el equipo Linux.
  - Fases: preparar el repo, montar Railway, mudar la base y plan de vuelta.
- RW-51: "Ve avanzando lo que falta, de la forma más escalable, considerando que igual haremos cambios" (el backend llevaba dos o tres días apagado): SPEC-B22 y ADR-B19.
- RW-52: "¿Podemos acceder a Railway, o lo puedes hacer desde la terminal?" (el usuario ya tenía el proyecto creado): sí, con la CLI (RW-15). Allí estaba el proyecto `KMV`, con el servicio conectado al repo (RW-01).
- RW-53: decisiones, con opciones: acceso público a la base sólo para copiar (DP-12), token de administrador (DP-11) y aviso de gasto a $8 (RW-03).
- RW-54: "¿Y estos?" (logs pegados): es el procesador en reposo, sin errores (RW-13b).
- RW-55: "¿Siempre tiene que repetirlo? ¿No hay forma de que Smartsheet nos avise?" y "¿No dará problemas? ¿Separamos las llamadas en un worker o un servicio aparte?": DP-13.
- RW-56: "`gis_permisos`, la gestión de usuarios y lo demás quedarán obsoletos: ¿no recomiendas webhooks para nada?": queda PEN-57. Hoy ninguna función necesita webhooks, ni los de Smartsheet ni unos propios; cuándo revisarlo, en DP-13.
- RW-57: prueba del usuario y "no salió el pedido de Records; revisa qué más faltó, crea tú un proyecto con subfilas y mantenlas": RW-06, RW-06b y RW-08. Queda la decisión K2-99.
- RW-58: "Documenta todo lo que se hizo y se preguntó desde un poco antes del despliegue": esta sección, la bitácora del día, y los estados al día en KMV_2.0 (K2-72, K2-85b, K2-91, K2-96d, K2-97 a K2-100), SPEC-B17, SPEC-B19, SPEC-B21, el mapa, `servicios/ids/README.md`, B-16, AUTOMATIZACIONES AU-07, VISTAS, ARQUITECTURA y el índice de docs.
- RW-59: "¿Qué pasa si borro filas?": K2-101 y mapa MP-92b. "Dejémoslo como está; al pasar a producción borramos toda la base": de acuerdo, con el orden de K2-102 (RW-60).
