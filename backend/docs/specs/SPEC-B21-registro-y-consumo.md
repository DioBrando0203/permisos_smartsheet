# SPEC-B21 Registro de eventos y consumo de API del servicio

Estado: implementada el 2026-11-23 (pedido del usuario: saber qué pasa y si hay errores, y que el servicio aguante la maestra 2.0 con todas las compañías; `KMV_2.0.md` K2-96 a K2-96c). En Railway desde el 2026-11-24 17:53 (despliegue de `74efda8`, PEN-56); sus logs se leen como explica `../DESPLIEGUE_RAILWAY.md` RW-13b.

## Contexto

- El servicio corre todo el día; se trabaja 8 horas. La maestra 2.0 reúne a todas las compañías (unas 6 329 filas por año) y Smartsheet admite 300 llamadas por minuto por token (sólo adjuntos e historial de celdas cuentan 10).
- Antes de este cambio: el registro sólo salía por consola; los fallos de un paso quedaban como tipo de error en `/api/ids/status` sin detalle en el registro; cada lectura de filas pedía páginas de 500 (13 pedidos por lectura a fin de año); cada paso releía sus hojas en cada pasada, cambiaran o no; la versión se consultaba cada 5 s también de noche.

## Comportamiento

- RG-01: registro en memoria con los últimos `APP_LOG_BUFFER_SIZE` eventos (1 000 por defecto) desde nivel INFO, además de la consola (que es lo que guarda Railway o AWS). Cada evento: hora UTC ISO, nivel, origen y mensaje. Se ocultan tokens (`Bearer ...`) y correos. Las líneas INFO de cada llamada a Smartsheet (`app.smartsheet`) no entran al registro en memoria (llenarían el espacio); entran sus advertencias y errores, y se cuentan en RG-04.
- RG-02: `GET /api/ids/logs`, con la misma autenticación que el ID Manager (`IDS_ADMIN_TOKEN`). Parámetros: `level` (`INFO`, `WARNING` o `ERROR`; por defecto `WARNING`), `limit` (1 a 500; por defecto 100), `contains` (texto, opcional). Devuelve los eventos del más nuevo al más viejo, la capacidad del registro y el consumo de API (RG-04).
- RG-03: si falla un paso del ciclo (catálogo, `Obs`, una hoja de equipo) o el ciclo entero, el fallo se registra como ERROR con el nombre del paso y la traza, además del tipo de error que ya muestra `/api/ids/status`.
- RG-04: consumo de API desde que arrancó el servicio: llamadas en el último minuto y en los últimos 60 minutos, total, respuestas 429 y esperas del freno (CA-02).
- CA-01: una lectura de filas pide la hoja completa en un solo pedido (sin `page` ni `pageSize`, comprobado el 2026-11-22: 2 287 filas en 0,9 s). Si Smartsheet devolviera menos filas que `totalRowCount`, sigue con páginas de 500 como antes.
- CA-02: freno propio en el transporte: no se envían más de `SMARTSHEET_MAX_REQUESTS_PER_MINUTE` (250 por defecto) en 60 s; si se llega, espera antes de enviar. Evita el 429 (300 por minuto) y deja margen a otros usos del token. No cambia concurrencia ni reintentos (SM-05).
- CA-03: los pasos de hojas de equipo, herencia, opciones, metraje y contactos se saltan si no cambió la versión de ninguna de las hojas que leen desde su última pasada correcta, y repiten su último resultado. Corren igual al menos cada `APP_STEPS_FORCE_SECONDS` (600). Una pasada con error no se recuerda: la siguiente vuelve a correr. Si no se puede leer la versión, el paso corre. La versión de cada hoja se lee una sola vez por pasada (vale 5 s) aunque varios pasos la usen.
- CA-04: `Obs` sigue la misma regla con su hoja, forzado al menos cada `APP_OBS_FORCE_SECONDS` (120): una conversación nueva se copia a lo sumo en ese tiempo aunque no cambie la versión de la hoja.
- CA-05: sin cambios en las hojas durante `IDS_MONITOR_IDLE_AFTER_SECONDS` (120), el monitor consulta la versión cada `IDS_MONITOR_IDLE_POLL_SECONDS` (30) en vez de cada `IDS_MONITOR_POLL_SECONDS`; con el primer cambio vuelve a la consulta rápida. El ciclo completo sigue corriendo al menos cada `IDS_MONITOR_INTERVAL_SECONDS`.

## Estimado (maestra 2.0 a fin de año)

- Antes: unas 200 llamadas por minuto sin trabajo y más de 300 en las horas de trabajo con cambios seguidos.
- Después: sin trabajo, la consulta de versión (2 por minuto) más el ciclo del ID Manager (1 a 2 lecturas por minuto) y las versiones de cada paso; en las horas de trabajo, una lectura por hoja y por pasada. Del orden de 15 por minuto sin trabajo y 30 a 60 en los picos. Pendiente para después (K2-96c): columnas en memoria, una sola lectura de la maestra compartida por los pasos, `rowsModifiedSince` y webhooks.

## Criterios de aceptación

- CA-B21-01: el registro guarda hasta su capacidad, oculta tokens y correos, filtra por nivel y texto, y no guarda las líneas INFO de `app.smartsheet`. Prueba: `test_logbook.py`.
- CA-B21-02: `GET /api/ids/logs` exige el token del ID Manager, valida `level` y `limit` y devuelve eventos y consumo. Prueba: `test_logs_route.py`.
- CA-B21-03: un paso que falla queda en el registro como ERROR con su nombre. Prueba: `test_ids_monitor.py::test_failed_step_is_logged`.
- CA-B21-04: `list_rows` hace un solo pedido sin paginar y pagina sólo si faltan filas. Prueba: `test_client.py::test_list_rows_reads_the_whole_sheet_in_one_request`, `::test_list_rows_falls_back_to_pages_when_rows_are_missing`.
- CA-B21-05: el freno espera al llegar al tope y cuenta llamadas, 429 y esperas. Prueba: `test_usage.py`.
- Verificación real (2026-11-23, sólo GET, con el cliente nuevo): `8. Crown Castle Fiber - Engineering Plan 2026`, 2 287 filas en un pedido (1,0 s); `PROJECT KMV 2.0 (Prototype)`, 15 filas (0,3 s); el conteo registró las 5 llamadas.
- CA-B21-06: un paso con versiones iguales se salta; con un cambio, con error previo, sin versión o pasado el forzado, corre; la versión se lee una vez por pasada. Prueba: `test_step_gate.py`.
- CA-B21-07: sin cambios, el monitor pasa a la consulta lenta y vuelve a la rápida con un cambio. Prueba: `test_ids_monitor.py::test_monitor_polls_slower_when_idle`.
