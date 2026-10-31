# Bloqueos y problemas conocidos (backend)

Formato: ID, fecha Lima, síntoma, causa, solución o prevención, estado.

## B-01 Escrituras de `/2.0/shares` sin verificar

Fecha: 2026-10-12. Estado: abierto (PEN-07).
Síntoma: POST, PATCH y DELETE de los endpoints unificados sólo están documentados.
Causa: no se escribe sobre hojas reales sin una hoja de prueba designada por el usuario.
Prevención: verificar en la hoja de prueba; si difieren, ajustar SPEC-B02 y ADR-B03 o usar los legados.

## B-02 `sharingInclude=ALL` no existe

Fecha: 2026-10-12. Estado: entendido.
Síntoma: 400 con `errorCode` 1018.
Causa: Smartsheet sólo acepta `ITEM`, `WORKSPACE` y `SUBJECT_DETAILS_PROFILE_IMAGE`, separados por coma.
Prevención: usar `sharingInclude=ITEM,WORKSPACE` (SPEC-B02).

## B-03 Nombre ausente en algunos permisos

Fecha: 2026-10-12. Estado: entendido.
Síntoma: un permiso de usuario llega sin `name`.
Causa: la persona no completó su perfil o es una invitación.
Prevención: `name` opcional en el contrato; el frontend muestra el correo como nombre.

## B-04 Token en un canal no seguro

Fecha: 2026-10-12. Estado: abierto; decide el usuario si rota el token.
Situación: el token se compartió en la conversación con el asistente para guardarlo en `backend/.env`.
Prevención: `.env` fuera del control de versiones; si hay duda de exposición, generar un token nuevo en Smartsheet y revocar el anterior.

## B-05 Mismo id para el permiso propio y el heredado

Fecha: 2026-10-12. Estado: entendido.
Síntoma: en una hoja real, el propietario aparece dos veces (`ITEM` y `WORKSPACE`) con el mismo `id` de permiso.
Causa: Smartsheet identifica el permiso por persona, no por origen.
Prevención: el frontend no puede usar `id` sola como clave de fila; usar `id` + `scope` (o agrupar por persona, UX-27). PATCH y DELETE actúan sobre el permiso propio y el backend comprueba el `scope` leído antes de escribir.

## B-06 `includeAll=true` no siempre trae todo

Fecha: 2026-10-12. Estado: resuelto (2026-10-16, PEN-23).
Síntoma: `GET /2.0/users/sheets?includeAll=true` devuelve 100 elementos con `totalPages=-1`, cuando con `pageSize=1000` hay 104.
Causa: ese endpoint no informa el total y corta en 100 pese a `includeAll`.
Prevención: para endpoints que respondan `totalPages=-1`, paginar por `page` hasta recibir menos de `pageSize`. Revisar `client._get_all` antes de usar `/users/sheets`. `/sheets`, `/contacts`, `/users` y `/groups` hoy devuelven totales coherentes.

## B-07 Dynamic View invisible para la API

Fecha: 2026-10-12. Estado: límite honesto (PEN-17).
Situación: Dynamic View permite compartir sólo ciertas filas y columnas sin compartir la hoja. No tiene API pública según respuestas de la comunidad de Smartsheet (no confirmado en la referencia oficial).
Consecuencia: el panel puede decir que una hoja tiene 10 personas con acceso y que alguien no tiene acceso, cuando además hay gente que la ve por una vista dinámica. Los administradores de una vista sí deben tener la hoja compartida como Propietario o Administrador, así que ellos sí aparecen.
Prevención: no afirmar en la interfaz "nadie más ve esta hoja"; decir "personas con la hoja compartida". Corrige lo dicho antes en conversación ("Smartsheet no tiene permisos por fila o columna"): sí los tiene, mediante Dynamic View.

## B-08 Sin registro de eventos de la cuenta en el plan

Fecha: 2026-10-16. Estado: límite del plan.
Síntoma: `GET /2.0/events` responde 403 `errorCode` 1013.
Causa: Event Reporting es un complemento de pago (premium add-on), aun en el plan Enterprise; según la documentación de Smartsheet sólo se ofrece en Enterprise y Advanced Work Management. El token es de un administrador del sistema (requisito cumplido), así que el 1013 indica que el complemento no está contratado. Verificado de nuevo el 2026-10-16 con `since`, `streamPosition` y `maxCount`: mismo 1013. La API no informa el plan de la cuenta.
Consecuencia: el panel no puede saber quién compartió, quitó un acceso o borró una fila. Sí puede leer la última modificación de cada fila y el historial de cada celda.
Prevención: no prometer un historial completo; si el plan cambia, `/events` sería la fuente principal (PEN-21).

## B-09 `includeAll` retirado en algunos endpoints

Fecha: 2026-10-16. Estado: resuelto (2026-10-16, PEN-23): el cliente ya no usa `includeAll`.
Síntoma: `GET /2.0/webhooks?includeAll=true` responde 400 `errorCode` 1018: "The 'includeAll' parameter has been deprecated… use pagination parameters".
Causa: Smartsheet está retirando `includeAll` en favor de `page` y `pageSize`.
Riesgo: `client._get_all` usa `includeAll=true` en `/sheets`, `/users`, `/contacts`, `/groups`, columnas e historial de celdas; hoy funcionan, pero pueden empezar a fallar igual. Junto con B-06 (corte en 100 sin avisar).
Prevención: cambiar `_get_all` a paginación explícita (`pageSize` y `page` hasta recibir menos que `pageSize`) con prueba; prioridad alta antes del frontend.

## B-10 httpx registraba URLs completas

Fecha: 2026-10-16. Estado: resuelto.
Síntoma: el log del servidor tenía líneas `HTTP Request: GET https://api.smartsheet.com/...?...` con la query completa.
Causa: httpx registra cada solicitud en INFO; `logging.basicConfig(level=INFO)` lo dejaba pasar.
Solución: `logging.getLogger("httpx").setLevel(WARNING)` en `main.py`; prueba `test_security.py::test_httpx_does_not_log_full_urls`.
Revisión: en los logs de prueba anteriores no había correos ni token (sólo ids y parámetros técnicos).

## B-11 Uvicorn huérfano y `.port` olvidado al cerrar por señal

Fecha: 2026-10-16. Estado: resuelto.
Síntoma: al detener `run.py` con una señal (`kill`, terminal cerrada) quedaba `backend/.port` y el puerto seguía ocupado.
Causa: la señal terminaba Python sin pasar por `finally`; además, matar de golpe al proceso principal de Uvicorn con `--reload` deja huérfano al que atiende el puerto.
Solución: `launcher.main` convierte SIGTERM en salida normal y `stop()` pide a Uvicorn que termine (y sólo si no responde en 10 s lo mata). Verificado: tras SIGTERM, sin `.port` y el 8710 libre.

## B-12 El backend no importa con Python 3.11 a 3.13

Fecha: 2026-10-30. Estado: abierto (prevención aplicada).
Síntoma: en un equipo Windows con Python 3.12, `pytest` no llega a correr: `app/services/sheets.py` falla al importar con `TypeError: 'function' object is not subscriptable`.
Causa: `SheetService` y `PeopleService` definen un método `list` y, más abajo en el cuerpo de la clase, anotan `-> list[...]` (`sheets.py` líneas 48, 57 y 85; `people.py` líneas 94, 98, 111 y 117). Hasta 3.13 las anotaciones se evalúan al definir la clase y `list` ya es el método; 3.14 las evalúa de forma diferida (PEP 649) y no lo nota. Por eso pasaba inadvertido en el equipo de desarrollo (3.14.4).
Prevención: crear el entorno con Python 3.14 (Windows: `py -3.14 -m venv .venv`); requisito corregido en `LEVANTAMIENTO.md`, `README.md` y `tecnologias/STACK.md`. Verificado en Windows con 3.14.7: 156 pruebas aprobadas.
Solución pendiente (decidir con el usuario): para cumplir `requires-python >=3.11` de `pyproject.toml`, anotar con `builtins.list` o renombrar los métodos `list`, y probar con 3.11; si no, subir `requires-python` a 3.14.

## B-13 FDACS no acepta conexiones desde el equipo Windows

Fecha: 2026-10-30. Estado: abierto (externo); mitigado por PEN-30.
Síntoma: el panel quedaba en "Consultando FDOT y FDACS…" unos 60 s y el punto llegaba sin parcela; en `sources`, `fdacs_parcels: timeout` con 60 566 ms.
Causa: `gis.fdacs.gov` resuelve por DNS (20.141.132.222) pero no completa la conexión TCP (curl: HTTP 000 a los 21 s), mientras FDOT responde en menos de 1 s desde la misma red. En el equipo Linux funcionó el mismo día a las 17:41; no se sabe si es una caída de FDACS o un bloqueo de esta red.
Mitigación: plazo de conexión de 5 s sin reintentos, pausa de 120 s para el host que no conecta y respaldo de parcelas de Broward (SPEC-B14, CA-14 y CA-15). Fuera de Broward el punto sigue sin parcela mientras FDACS no responda.

## B-14 `run.py --reload` no termina de recargar en Windows

Fecha: 2026-10-30. Estado: abierto.
Síntoma: tras editar un archivo, Uvicorn escribe "WatchFiles detected changes … Reloading..." pero no aparece un "Started server process" nuevo y el puerto sigue sirviendo el código anterior (visto dos veces, con consultas al mapa en curso).
Causa: no confirmada; ocurrió mientras había solicitudes abiertas (una esperaba a FDACS 60 s).
Prevención: tras cambiar el backend, comprobar en el log que arrancó un proceso nuevo; si no, detener `run.py` y volver a ejecutarlo. Al detenerlo no quedaron procesos huérfanos y el 8710 quedó libre (comprobado con `netstat` y `wmic`).

## B-15 El firewall del Censo bloquea la IP tras ráfagas de consultas

Fecha: 2026-10-31. Estado: mitigado; el bloqueo es del proveedor.
Síntoma: `/api/map/search` respondía 500 en Fort Lauderdale; TIGERweb y el geocodificador del Censo devolvían HTTP 200 con una página HTML "Request Rejected" (189 a 247 bytes) a cualquier consulta, también a los metadatos; el FDOT seguía respondiendo.
Causa: unas decenas de consultas seguidas desde el equipo (cada búsqueda con zona y cruce pide hasta seis a TIGER, una por pausa al escribir, más las pruebas manuales). El transporte llamaba a `response.json()` sin protección y el HTML tumbaba la búsqueda.
Solución: el HTML cuenta como fuente caída y el host se salta `gis_unreachable_cooldown_seconds`; las líneas TIGER se cachean por zona y filtro; el buscador espera 500 ms en vez de 350 (SPEC-B14 CA-22). Prevención: no hacer ráfagas de pruebas contra census.gov; el bloqueo se levanta solo, sin plazo publicado.

