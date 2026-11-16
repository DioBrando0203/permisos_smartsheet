# SPEC-B20 Hojas de proceso (maestra 2.0)

Estado: implementada y probada en el prototipo de Pruebas (2026-11-16 16:41, PEN-54); desde el 2026-11-16 16:50 `backend/.env` apunta a la maestra 2.0 del prototipo (pedido del usuario; valores de la 1.0.0 comentados al final para volver). Mismo mecanismo que Records y Facturación (SPEC-B18, SPEC-B19), en `services/childsheets/`. IDs de la maestra 2.0 en SPEC-ID01 ID-52 a ID-54.

## Objetivo

- HP-01: en la maestra 2.0 la fila madre es el proyecto y cada hija es un proceso según su `Type of Project`; el detalle de cada proceso vive en su hoja: `Permits` (hijas `KMV-Permit` y `KMV-Line`, equipo de permisos) y `MOT & Packages` (hijas `KMV-MOT` y paquetes de cada proyecto, persona de MOT). La coordinadora trabaja sólo con Dynamic Views; el servicio indenta, numera, copia y resume (ADR-B15: Smartsheet sigue siendo la fuente de verdad y nadie cambia de herramienta).

## Reglas

- HP-02: una hija pasa a `Permits` cuando tiene `Type of Project` `KMV-Permit` o `KMV-Line`, ID (Tracking Project canónico) y `Agency`, y no está en `NO PERMIT REQUIRED` ni `CANCELLED`; si después pasa a requerir permiso o recibe su agencia, pasa en ese momento. A `MOT & Packages` pasa una hija `KMV-MOT` con las mismas condiciones (fila `MOT`) y una madre con `Prepare Packages` (fila `Package`). Las madres `KMV-P` y `KMV-Miscellaneous` no generan fila de proceso salvo `Package`. Una fila por fila de la maestra, nunca se borra.
- HP-03: contexto copiado y siempre al día (bloqueado en la hoja de proceso): `Tracking Project`, tipo (en `Permits`), `Agency`, `Permitting Team`, `Customer`, `Project Name`, `Project Address`, `City`, `County`, `Designers`, `Contractor`, `Date Received`, `PM Approval Date` y, en `Permits`, `Design Ticket` y `Mile Post`; `Row Type` (`MOT` o `Package`) en `MOT & Packages`. `LT` se copia una sola vez al crear la fila.
- HP-04: si la hija de la maestra tiene vacía una columna de contexto del proyecto, la hoja de proceso toma la de su madre (por ejemplo `Permitting Team` o `Designers`).
- HP-05: resumen que vuelve a la hija de la maestra (nunca a la madre): el estado de la hoja (`Permit Status` o `MOT Status`) a `Project Status`, y `Permit #`, `Permit Approved`, `Permit Expires`, `Permit Fee`, `Custom MOT`, `TYPICAL MOT`. La hoja de proceso es la fuente de verdad: un cambio a mano en la hija de la maestra se reescribe. Nunca vuelve a una columna que en la maestra es fórmula.
- HP-06: cancelación (decisión del usuario, 2026-11-16): las hijas no se borran; si la maestra pone `CANCELLED` en `Project Status` de la fila, el servicio pone `CANCELLED` en el estado de su fila de proceso y no lo devuelve encima. Para reactivarla, el equipo cambia el estado en su hoja.
- HP-07: herencia en la maestra: cada hija completa sus celdas vacías con las de su proyecto (`Customer`, `Project Name`, `Project Address`, `City`, `County`, `CC System`, `Date Received`, `Survey Completed`, `Design Completed`, `PM Approval Date`, `LT`); nunca reemplaza un valor y nunca escribe en fórmulas. Así una hija creada desde una vista y movida bajo su proyecto (ID-51) queda completa, como cuando se copiaba la madre.
- HP-08: cambio de tipo (decisión del usuario): la fila se moverá a la otra hoja con las columnas del mismo nombre. Pendiente de implementar: hoy la fila se queda en su hoja y la nueva hoja crea otra.
- HP-09: barreras: escritura aprobada (las del ID Manager), hojas configuradas y dentro de Pruebas; columnas requeridas presentes una sola vez; tope de filas por pasada (`APP_RECORDS_MAX_ROWS`). Nada técnico visible: el vínculo es `Master Row`, oculta.

- HP-14 (2026-11-16 17:56, pedido del usuario): hoja `Design Tickets` para que el responsable (`DT Owner`) llene `Design Ticket` y `Mile Post`: una fila por fila de la maestra con `DT Owner` asignado; contexto `Tracking Project`, `DT Owner`, `Project Status`, `Customer`, `Project Name`, `Project Address`, `City`, `County`, `Date Received`, `Designers`; `Design Ticket` y `Mile Post` se copian una vez al crear y luego vuelven a la maestra (la hoja manda; en la maestra quedan bloqueadas). Variables `APP_DESIGN_TICKETS_SYNC_ENABLED` y `APP_DESIGN_TICKETS_SHEET_ID`. Prototipo: `Design Tickets (Prototype)` `263146012102532` (13 columnas), reporte `KMV 2.0 | Design Tickets` `1458545469116292`.

## Configuración

- HP-10: variables (`backend/.env`, ver `.env.example`): `APP_PERMITS_SYNC_ENABLED` y `APP_PERMITS_SHEET_ID`, `APP_MOT_SYNC_ENABLED` y `APP_MOT_SHEET_ID`, `APP_INHERIT_ENABLED`; para la maestra 2.0 además `IDS_MASTER_SHEET_ID`, `IDS_PROJECT_FORMAT=year`, `IDS_PROJECT_OPTIONS_ENABLED=true`, `IDS_CUSTOMER_CHANGE_ENABLED=true` (activa ID-51) y los ids de sus Records y Billing. Orden de los pasos en cada ciclo: herencia, Records, Billing, `Permits`, `MOT & Packages`, `Design Tickets` y listas de proyectos.

## Prototipo

- HP-11: carpeta `Pruebas/Producto/PROJECT KMV 2.0 - Prototype`: maestra `1979884168761220` (78 columnas: desde el 2026-11-16 18:35 vuelve el metraje, SPEC-B19 FH-05b), `Permits (Prototype)` `3435959686483844`, `MOT & Packages (Prototype)` `2866571577085828`, `Records Requests (Prototype)` `3471473697312644`, `Billing (Prototype)` `4630718656499588`; reportes `KMV 2.0 | ...` en su carpeta `Reports` (detalle en PEN-54).

## Pruebas

- HP-12: `tests/test_process_sheets.py` (13 pruebas: reglas de paso, contexto del proyecto, resumen sólo a hijas, cancelación, filas `MOT` y `Package`, herencia, listas y orden de los pasos) y `tests/test_id_year_format.py` (4: formato, contador único por año, hija de otro cliente que sigue a su madre, permiso suelto sin número que pasa bajo su proyecto).
