# SPEC-B18 Hoja hija de Records

Estado: en uso en Pruebas (prueba real correcta el 2026-11-13 10:20, PEN-49). Primera hoja hija. Desde el 2026-11-13 el mecanismo es genérico (`services/childsheets/`, definición en `specs.py`) y lo comparte Facturación (SPEC-B19); el resultado sigue en `last_records_sync`.

## Objetivo

- RH-01: el trabajo de Records vive en su propia hoja, `Records Requests` (`7578012825636740`, `Pruebas/Producto/PROJECT KMV`), separado de permisos y diseño, porque en `Permitting Team` a veces una persona hace Records y otra permisos (decisión del usuario). La maestra sólo indica qué filas necesitan Records con la casilla `Records Needed`.
- RH-02 (ADR-B15): Smartsheet no crea filas en otra hoja por cada fila marcada manteniendo el vínculo; "Copy rows" copia la fila entera, agrega al destino las columnas que faltan y no actualiza después. El servicio crea y mantiene esas filas; Smartsheet sigue siendo la fuente de verdad.

## Hojas

- RH-03: maestra: `IDS_MASTER_SHEET_ID` (hoy PROJECT KMV 1.0.0), con la casilla `Records Needed`. Hoja hija: `APP_RECORDS_SHEET_ID`.
- RH-03b (2026-11-16 17:38, decisión del usuario, PEN-54): Records siempre se pide a una agencia: la fila se crea cuando la fila de la maestra tiene `Records Needed` o `Records Owner` y además `Agency`; sin agencia espera y se crea en cuanto la tiene. En 2026 el trabajo de Records estuvo en hijas con agencia (`Record Request` 582 de 585 hijas con agencia; en madres 26 de 239), así que se marca en la fila del permiso. Las filas ya creadas sin agencia no se borran.
- RH-03c (2026-11-16 18:56, pedido del usuario, maestra 2.0): columna `Records Status` en la maestra, fórmula de columna con dos referencias a la hoja de Records (`Records Requests Tracking` y `Records Requests Status`): por `Tracking Project` cuenta los pedidos y muestra `Received` (todos cerrados y alguno recibido), `No records` (todos cerrados sin recibir; cerrados = `Received`, `No records`, `Not Appy`) o `Pending (n/m received)`; vacío sin pedidos. La calcula Smartsheet (sin servicio), con 15 a 30 segundos de demora entre hojas. Sirve para que diseño sepa si llegaron los Records de su proyecto en una sola fila.
- RH-03d (2026-11-24, pedido del usuario: que diseño vea en su vista cuando el Records ya está todo hecho): `Records Status` muestra `Complete` cuando todos los pedidos de Records del proyecto tienen `Record Box` marcado (en las hojas 2026 la casilla se marca cuando el Records ya está resuelto); si no, sigue la regla de RH-03c. Tercera referencia a la hoja de Records: `Records Requests Box` (columna `Record Box`). La maestra sigue con 79 columnas. Fórmula anterior, para volver atrás: `=IFERROR(IF(COUNTIF({Records Requests Tracking}, [Tracking Project]@row) = 0, "", IF(COUNTIFS({Records Requests Tracking}, [Tracking Project]@row, {Records Requests Status}, OR(@cell = "Received", @cell = "No records", @cell = "Not Appy")) = COUNTIF({Records Requests Tracking}, [Tracking Project]@row), IF(COUNTIFS({Records Requests Tracking}, [Tracking Project]@row, {Records Requests Status}, "Received") > 0, "Received", "No records"), "Pending (" + COUNTIFS({Records Requests Tracking}, [Tracking Project]@row, {Records Requests Status}, "Received") + "/" + COUNTIF({Records Requests Tracking}, [Tracking Project]@row) + " received)")), "")`.
- RH-04 (desde el 2026-11-13 16:45 el responsable se llama `Records Owner` en las dos hojas; antes `Record Request Assignment`, y antes `Designer2`): columnas de la hoja hija. Contexto, bloqueadas y escritas por el servicio: `Tracking Project` (principal), `Customer`, `Agency`, `Project Name`, `Project Address`, `City`, `County`, `Date Received`. Trabajo de Records, editadas por el equipo: `Records Owner` (responsable del pedido de Records: contexto copiado de la maestra y bloqueado; antes `Designer2`), `Request Type`, `Send Method`, `Record Request`, `Reminder Sent`, `LT Records`, `Future Project #`, `PRR #`, `Security Key`, `Record Received`, `Records Status`, `Record Box`, `Record # Days` (fórmula). Técnica, oculta y bloqueada: `Master Row` (id de la fila de la maestra).

## Reglas

- RH-05 (desde el 2026-11-13: también basta con asignar a alguien en `Records Owner`, columna de contacto de la maestra con las personas activas con correo; el aviso al asignado es una automatización de la maestra): una fila de la maestra con `Records Needed` marcada y un Tracking Project canónico (no vacío ni `Pending ID`) recibe una fila en la hoja hija, una sola vez: el vínculo es `Master Row`. Madres e hijas por igual. Sin ID todavía, espera.
- RH-06 (desde el 2026-11-13 la maestra ya no tiene las columnas de Records salvo `Designer2`, así que sólo se copian el contexto y `Designer2`): al crearla se copian el contexto y, una sola vez, los valores de Records que ya tenga la fila de la maestra (las columnas de RH-04 con el mismo título que existan en ella); desde entonces la hoja hija es la fuente de esos datos. Excepción (2026-11-24): `Records Status` no se copia: en la maestra 2.0 es el resumen calculado del proyecto (RH-03c, RH-03d), no el estado del pedido, y un pedido nuevo nacía con el resumen de los anteriores (por ejemplo `Received`). Prueba: `test_childsheets.py::test_records_status_summary_is_not_copied_to_a_new_request`.
- RH-07: el contexto se mantiene al día: si cambia en la maestra (por ejemplo, el Tracking Project tras un cambio de cliente, o el nombre del proyecto), se reescribe en la hoja hija, aunque la casilla ya no esté marcada.
- RH-08: nunca borra. Desmarcar la casilla o borrar la fila de la maestra no toca la fila de Records; volver a marcar reutiliza la misma fila. Una fila copiada en la maestra es otra fila: si lleva la casilla marcada, recibe su propia fila de Records.
- RH-09: nada técnico a la vista: `Master Row` va oculta; el servicio no escribe notas ni comentarios.

## Barreras y ejecución

- RH-10: `APP_RECORDS_SYNC_ENABLED=true`, `APP_RECORDS_SHEET_ID` y las barreras de escritura del ID Manager; las dos hojas en el workspace Pruebas, comprobado en cada pasada; columnas de contexto, `Master Row` y `Records Needed` presentes una sola vez. Si falta algo, no escribe.
- RH-11: corre al final de cada ciclo del procesador en modo asignación, como máximo cada `APP_RECORDS_INTERVAL_SECONDS` (30) y hasta `APP_RECORDS_MAX_ROWS` filas nuevas y otras tantas actualizaciones por pasada; el resto queda para la siguiente. Resultado en `last_records_sync` de `/api/ids/status`; un fallo no afecta a IDs, catálogo ni Obs.

## Criterios de aceptación

- CA-01: fila marcada con ID crea su fila con contexto, valores iniciales y `Master Row`; una segunda pasada no escribe.
- CA-02: fila marcada con `Pending ID` espera; fila sin marcar no crea.
- CA-03: cambio de contexto en la maestra se refleja; desmarcar no borra.
- CA-04: sin barreras, con una hoja fuera de Pruebas o sin las columnas no escribe; intervalo entre pasadas; un fallo queda aislado en el procesador.
