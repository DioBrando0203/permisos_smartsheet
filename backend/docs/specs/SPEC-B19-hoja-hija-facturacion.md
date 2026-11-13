# SPEC-B19 Hoja hija de Facturación

Estado: en prueba (2026-11-13, PEN-49). Mismo mecanismo que Records (SPEC-B18), en `services/childsheets/`.

## Objetivo

- FH-01: la facturación tiene su propia hoja, `Billing` (`3091384761536388`, `Pruebas/Producto/PROJECT KMV`), con todo lo que necesita el responsable de facturación en la misma fila, como los reportes `... - Generator` que usa hoy (sólo lectura, prohibido modificarlos). Su vista será un reporte sobre esta hoja con el filtro del generador: `Invoice? GALP` sin marcar y `PM Approval Date` con fecha.
- FH-02 (ADR-B15): Smartsheet no mantiene una fila de otra hoja por cada fila de la maestra con contexto al día; el servicio lo hace y nunca borra.

## Reglas

- FH-03: cada fila de la maestra con Tracking Project canónico recibe su fila en `Billing` desde que nace (sin casilla), madres e hijas, para que diseño pueda llenar las cantidades antes de facturar.
- FH-04: contexto copiado de la maestra, bloqueado en `Billing` y siempre al día: `Tracking Project`, `Customer`, `Type of Project`, `CC System`, `Project Status`, `Project Name`, `Project Address`, `City`, `County`, `PM Approval Date`, `Construction Manager` (nombre como texto), `Agency`, `Contractor`, `Permit #`, `Permit Fee`, `Stamp And Signatures #` y las 12 cantidades (`Total Footage`, `UG`, `UG + Profile`, `ISP`, `Aerial`, `Custom MOT`, `TYPICAL MOT`, `Additional Site Survey`, `Survey Certified`, `Tone Locating`, `Sonde FTG`, `GPR`). Las cantidades siguen en la maestra hasta volver a preguntar al usuario (decisión del 2026-11-13). `Row Type` la calcula el servicio: `Project` (madre) o `Permit` (hija), para los colores.
- FH-05: columnas de facturación, que se trabajan en `Billing`: `Purchase Orden`, `Invoice? GALP`, `Invoice? KMV`, `Customer invoice?`, `Invoice Completed (Galp)`, `PM Approval Invoice Date`, `Invoice Sent`, `Invoice Paid`; fórmulas `Invoice # Days` (vacío en vez de `#INVALID DATA`) e `Invoice Status`. Al crear la fila se copian una vez los valores que ya tenga la maestra.
- FH-06: resumen: `Invoice Status` vuelve de `Billing` a la maestra, sólo si en la maestra esa columna no es fórmula (hoy lo es: no se escribe hasta que se quite al migrar).
- FH-07: nada técnico a la vista; `Master Row` oculta; nunca borra; colores con las mismas reglas de la maestra (estado y madre o hija), creados por el usuario en la interfaz.

## Barreras y ejecución

- FH-08: `APP_BILLING_SYNC_ENABLED=true`, `APP_BILLING_SHEET_ID` y las barreras de escritura; las dos hojas en Pruebas; columnas requeridas una sola vez. Intervalo y tope de filas: los de Records (`APP_RECORDS_INTERVAL_SECONDS`, `APP_RECORDS_MAX_ROWS`). Resultado en `last_billing_sync`.

## Criterios de aceptación

- CA-01: toda fila con ID crea su fila, con `Row Type` y valores iniciales; `Pending ID` espera.
- CA-02: el contexto sigue a la maestra.
- CA-03: el resumen vuelve sólo a una columna de la maestra que no es fórmula.
- CA-04: barreras y aislamiento en el procesador, como SPEC-B18.
