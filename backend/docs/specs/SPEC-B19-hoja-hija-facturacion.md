# SPEC-B19 Hoja hija de Facturación

Estado: en uso en Pruebas (prueba real correcta el 2026-11-13 12:11, PEN-49); maestra migrada el 2026-11-13 12:25: sin las columnas de factura e `Invoice Status` como resumen escrito por el servicio (FH-06 activo). Desde el 2026-11-13 23:06 (pedido del usuario) el metraje se trabaja en `Billing` y `Designers` se copia para la vista de diseño (FH-05, FH-09); falta reiniciar el backend y borrar el metraje de la maestra. Mismo mecanismo que Records (SPEC-B18), en `services/childsheets/`.

## Objetivo

- FH-01: la facturación tiene su propia hoja, `Billing` (`3091384761536388`, `Pruebas/Producto/PROJECT KMV`), con todo lo que necesita el responsable de facturación en la misma fila, como los reportes `... - Generator` que usa hoy (sólo lectura, prohibido modificarlos). Su vista será un reporte sobre esta hoja con el filtro del generador: `Invoice? GALP` sin marcar y `PM Approval Date` con fecha.
- FH-02 (ADR-B15): Smartsheet no mantiene una fila de otra hoja por cada fila de la maestra con contexto al día; el servicio lo hace y nunca borra.

## Reglas

- FH-03: cada fila de la maestra con Tracking Project canónico recibe su fila en `Billing` desde que nace (sin casilla), madres e hijas, para que diseño pueda llenar las cantidades antes de facturar.
- FH-04: contexto copiado de la maestra, bloqueado en `Billing` y siempre al día: `Tracking Project`, `Customer`, `Type of Project`, `CC System`, `Project Status`, `Project Name`, `Project Address`, `City`, `County`, `PM Approval Date`, `Construction Manager` (nombre como texto), `Agency`, `Contractor`, `Permit #`, `Permit Fee`, `Stamp And Signatures #`, `Designers` (FH-09) y las 7 cantidades que siguen en la maestra (`Custom MOT`, `TYPICAL MOT`, `Additional Site Survey`, `Survey Certified`, `Tone Locating`, `Sonde FTG`, `GPR`). `Row Type` la calcula el servicio: `Project` (madre) o `Permit` (hija), para los colores.
- FH-05: columnas que se trabajan en `Billing`: el metraje que llena diseño (`Total Footage`, `UG`, `UG + Profile`, `ISP`, `Aerial`, desbloqueadas) y las de facturación: `Purchase Orden`, `Invoice? GALP`, `Invoice? KMV`, `Customer invoice?`, `Invoice Completed (Galp)`, `PM Approval Invoice Date`, `Invoice Sent`, `Invoice Paid`; fórmulas `Invoice # Days` (vacío en vez de `#INVALID DATA`) e `Invoice Status`. Al crear la fila se copian una vez los valores que ya tenga la maestra.
- FH-06: resumen: `Invoice Status` vuelve de `Billing` a la maestra, sólo si en la maestra esa columna no es fórmula (hoy lo es: no se escribe hasta que se quite al migrar).
- FH-09: vista de diseño (decisión del usuario, 2026-11-13): una Dynamic View sobre un reporte con la maestra y `Billing`, restringida por `Designers`; cada proyecto sale en dos filas (estado en la maestra, metraje en `Billing`). Por eso `Billing` lleva `Designers` (varios contactos, bloqueada), copiada de la maestra con sus correos; un nombre sin correo no se copia, porque esa persona no puede entrar a la vista. La API sólo muestra el tipo y los correos de varios contactos con `level=2`, que el servicio pide en columnas y filas de las dos hojas.
- FH-07: nada técnico a la vista; `Master Row` oculta; nunca borra; colores con las mismas reglas de la maestra (estado y madre o hija), creados por el usuario en la interfaz.

## Barreras y ejecución

- FH-08: `APP_BILLING_SYNC_ENABLED=true`, `APP_BILLING_SHEET_ID` y las barreras de escritura; las dos hojas en Pruebas; columnas requeridas una sola vez. Intervalo y tope de filas: los de Records (`APP_RECORDS_INTERVAL_SECONDS`, `APP_RECORDS_MAX_ROWS`). Resultado en `last_billing_sync`.

## Criterios de aceptación

- CA-01: toda fila con ID crea su fila, con `Row Type` y valores iniciales; `Pending ID` espera.
- CA-02: el contexto sigue a la maestra.
- CA-03: el resumen vuelve sólo a una columna de la maestra que no es fórmula.
- CA-04: barreras y aislamiento en el procesador, como SPEC-B18.
- CA-05: el metraje se copia una sola vez al crear la fila; lo que diseño cambie en `Billing` no se pisa, y sin esas columnas en la maestra la pasada sigue sin errores.
- CA-06: `Designers` llega a `Billing` como varios contactos con sus correos, en orden y sin repetidos, y sigue a la maestra.
