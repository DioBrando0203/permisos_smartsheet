# SPEC-B18 Hoja hija de Records

Estado: en uso en Pruebas (prueba real correcta el 2026-11-13 10:20, PEN-49). Primera hoja hija. Desde el 2026-11-13 el mecanismo es genérico (`services/childsheets/`, definición en `specs.py`) y lo comparte Facturación (SPEC-B19); el resultado sigue en `last_records_sync`.

## Objetivo

- RH-01: el trabajo de Records vive en su propia hoja, `Records Requests` (`7578012825636740`, `Pruebas/Producto/PROJECT KMV`), separado de permisos y diseño, porque en `Permitting Team` a veces una persona hace Records y otra permisos (decisión del usuario). La maestra sólo indica qué filas necesitan Records con la casilla `Records Needed`.
- RH-02 (ADR-B15): Smartsheet no crea filas en otra hoja por cada fila marcada manteniendo el vínculo; "Copy rows" copia la fila entera, agrega al destino las columnas que faltan y no actualiza después. El servicio crea y mantiene esas filas; Smartsheet sigue siendo la fuente de verdad.

## Hojas

- RH-03: maestra: `IDS_MASTER_SHEET_ID` (hoy PROJECT KMV 1.0.0), con la casilla `Records Needed`. Hoja hija: `APP_RECORDS_SHEET_ID`.
- RH-04: columnas de la hoja hija. Contexto, bloqueadas y escritas por el servicio: `Tracking Project` (principal), `Customer`, `Agency`, `Project Name`, `Project Address`, `City`, `County`, `Date Received`. Trabajo de Records, editadas por el equipo: `Designer2` (responsable; se renombrará), `Email Designer2` (fórmula desde Contact List), `Request Type`, `Send Method`, `Record Request`, `Reminder Sent`, `LT Records`, `Future Project #`, `PRR #`, `Security Key`, `Record Received`, `Records Status`, `Record Box`, `Record # Days` (fórmula). Técnica, oculta y bloqueada: `Master Row` (id de la fila de la maestra).

## Reglas

- RH-05: una fila de la maestra con `Records Needed` marcada y un Tracking Project canónico (no vacío ni `Pending ID`) recibe una fila en la hoja hija, una sola vez: el vínculo es `Master Row`. Madres e hijas por igual. Sin ID todavía, espera.
- RH-06 (desde el 2026-11-13 la maestra ya no tiene las columnas de Records salvo `Designer2`, así que sólo se copian el contexto y `Designer2`): al crearla se copian el contexto y, una sola vez, los valores de Records que ya tenga la fila de la maestra (las columnas de RH-04 con el mismo título que existan en ella); desde entonces la hoja hija es la fuente de esos datos.
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
