# Vistas (Dynamic View) de la versión 2.0

Guía para armar las vistas de cada equipo sobre los reportes de `Pruebas/Producto/PROJECT KMV 2.0 - Prototype/Reports`. Los nombres de vistas, columnas y filtros van en inglés, como todo en Smartsheet. Reglas del servicio en SPEC-B20 y PEN-54.

## Idea general: que no canse la vista

- VK-01: la tabla muestra pocas columnas (6 a 8): las que sirven para encontrar la fila y saber qué falta. Todo lo demás va al panel de detalle, que se abre al hacer clic en la fila.
- VK-02: orden de izquierda a derecha, siempre el mismo en todas las vistas: quién es (ID y tipo), qué es (nombre), cómo está (estado), qué toca ahora (la fecha que sigue) y quién lo lleva.
- VK-03: el panel de detalle se divide en secciones con título, en el orden en que se trabaja: primero los datos del proyecto (sólo lectura), luego el trabajo del equipo (editable) y al final el estado.
- VK-04: lo que copia el servicio se marca de sólo lectura en la vista (contexto del proyecto, IDs, resúmenes). Si alguien lo cambia, el servicio lo vuelve a escribir: mejor que ni se pueda.
- VK-05: nunca se muestran columnas técnicas: `Master Row`, `Stable Tracking Project`, `Row Level`, `Row Order`, `Customer Code`, `Year`, `Control Linked Tracking`, ni `Primary` (siempre dice `KMV-P`).
- VK-06: cada vista abre con un filtro de lo pendiente (sin cerrados ni cancelados) y otro de todo; orden por `Tracking Project` de mayor a menor (lo más nuevo arriba).
- VK-07: si tu Dynamic View permite varios paneles de detalle con condición, usa uno por tipo de fila (por ejemplo, uno para proyectos y otro para permisos); así cada fila muestra sólo sus campos.
- VK-08: en cada vista de equipo, `Restrict by` (filtrar por persona) con su columna de asignación: cada uno ve sólo lo suyo.

## 1. Coordinación (Zaira): dos vistas

Recomiendo dos vistas sobre el mismo reporte en lugar de una con todos los campos: una para crear y llevar proyectos y otra para crear permisos. El formulario de cada una queda corto.

Reporte: `KMV 2.0 | Coordinator`. Hoja donde se guardan las filas nuevas: `PROJECT KMV 2.0 (Prototype)`.

### 1A. `KMV 2.0 | Projects`

- VK-10: filtro de la vista: `Type of Project` es `KMV-P` o `KMV-Miscellaneous`.
- VK-11: tabla, en este orden: `Tracking Project`, `Type of Project`, `Customer`, `Project Name`, `Project Status`, `Date Received`, `Drawing Due Date`, `Designers`, `Permitting Team`.
- VK-12: filtros guardados: `Open` (`Project Status` no es `COMPLETE` ni `CANCELLED`), `Pending ID` (`Tracking Project` es `Pending ID`), `All`.
- VK-13: formulario para crear un proyecto, en este orden y con obligatorios marcados (*):
  - `Type of Project` * (`KMV-P` o `KMV-Miscellaneous`)
  - `Customer` *
  - `Date Received` *
  - `Project Name` *
  - `Project Address`, `City`, `County`
  - `Task`, `Priority`, `CC System`
  - `Drawing Due Date`
  - `Designers` (proyecto de diseño) o `Permitting Team` (proyecto de permisos)
  - `Linked Tracking` (sólo si continúa un proyecto anterior)
  - Texto de ayuda en el formulario: "The project number appears in a minute (Pending ID until then)."
- VK-14: panel de detalle:
  - Sección `Project` (editable): `Type of Project`, `Customer`, `Project Name`, `Project Address`, `City`, `County`, `Task`, `Priority`, `CC System`, `Linked Tracking`.
  - Sección `Assignment` (editable): `Designers`, `Permitting Team`, `Surveyor`, `Engineer`, `Records Needed`, `Records Owner`, `Prepare Packages`, `DT Owner`, `Construction Manager`, `Contractor`.
  - Sección `Milestones` (editable): `Date Received`, `Drawing Due Date`, `Survey Completed`, `Design Completed`, `PM Approval Date`, `LT`, `Design Ticket`, `Mile Post`.
  - Sección `Status` : `Project Status` (editable); `Tracking Project` e `Invoice Status` (sólo lectura).
  - Sección `Notes` (sólo lectura): `Obs`.

### 1B. `KMV 2.0 | Permits Intake`

- VK-15: filtro de la vista: `Type of Project` es `KMV-Permit`, `KMV-Line` o `KMV-MOT`.
- VK-16: tabla: `Tracking Project`, `Parent Project`, `Type of Project`, `Agency`, `Project Status`, `Permitting Team`, `Project Name`.
- VK-17: formulario para crear un permiso, línea o MOT (corto a propósito):
  - `Type of Project` * (`KMV-Permit`, `KMV-Line` o `KMV-MOT`)
  - `Parent Project` * (el proyecto al que pertenece; la lista se actualiza sola)
  - `Agency` * (sin agencia la fila no pasa a la hoja del equipo)
  - `Permitting Team` (si se deja vacío, toma el del proyecto)
  - `Project Status` (sólo si nace como `NO PERMIT REQUIRED`)
  - Texto de ayuda: "It moves under its project and takes its data in about a minute."
- VK-18: panel de detalle: `Type of Project`, `Parent Project`, `Agency`, `Permitting Team`, `Contractor` editables; `Project Status`, `Permit #`, `Permit Approved`, `Permit Expires` de sólo lectura (vienen de la hoja del equipo), salvo `Project Status` para cancelar: `CANCELLED` en la fila cancela también en la hoja del equipo.

## 2. Diseño: `KMV 2.0 | Design`

Reporte: `KMV 2.0 | Design` (cada proyecto sale en dos filas: la de la maestra y la de `Billing` con el metraje).

- VK-20: `Restrict by`: `Designers`.
- VK-21: tabla: `Tracking Project`, `Sheet Name` (angosta, para distinguir las dos filas), `Project Name`, `Customer`, `Project Status`, `Drawing Due Date`, `QC IN`, `QC OUT`, `Total Footage`.
- VK-22: filtros guardados: `Open` (`Project Status` no es `COMPLETE` ni `CANCELLED`), `Needs QC` (`Project Status` es `2. Design Needs QC`), `All`.
- VK-23: sin formulario de filas nuevas.
- VK-24: panel de detalle:
  - Sección `Project` (sólo lectura): `Tracking Project`, `Project Name`, `Customer`, `Type of Project`, `Date Received`.
  - Sección `Design` (editable; sólo en la fila de la maestra): `Project Status`, `Drawing Due Date`, `Survey Completed`, `QC IN`, `QC OUT`, `Design Completed`, `Design Ticket`, `Mile Post`.
  - Sección `Footage` (editable; sólo en la fila de `Billing`): `Total Footage`, `UG`, `UG + Profile`, `ISP`, `Aerial`.
  - Si se puede poner condición al panel: panel `Design` cuando `Sheet Name` es la maestra y panel `Footage` cuando es `Billing`.

## 3. Permisos: `KMV 2.0 | Permits`

Reporte: `KMV 2.0 | Permits` (filas de `Permits` y, además, los proyectos `KMV-Miscellaneous` del equipo).

- VK-30: `Restrict by`: `Permitting Team`.
- VK-31: tabla: `Tracking Project`, `Type of Project`, `Agency`, `Permit Status`, `Project Name`, `Submitted Date`, `Permit #`, `Permit Expires`.
- VK-32: filtros guardados: `Open` (`Permit Status` no es `CANCELLED`, `4. Permit Closed`, `4. No Permit Required` ni `8. Close - Permit Process`), `In revision` (`Permit Status` es `4. Permit Needs Revision`), `Expiring` (`Permit Expires` en los próximos 30 días), `My projects` (`Type of Project` es `KMV-Miscellaneous`), `All`.
- VK-33: vista de tarjetas por `Permit Status` (columnas tipo tablero), para mover cada permiso de estado arrastrando.
- VK-34: sin formulario de filas nuevas: las crea el servicio desde la vista de coordinación.
- VK-35: panel de detalle de un permiso:
  - Sección `Permit` (sólo lectura): `Tracking Project`, `Type of Project`, `Agency`, `Customer`, `Project Name`, `Project Address`, `City`, `Design Ticket`, `Mile Post`, `Designers`, `Date Received`, `PM Approval Date`.
  - Sección `Application` (editable): `LT`, `App Sent to Contractor`, `App Returned from Contractor`, `Submitted Date`, `Runner Submitting`.
  - Sección `Revisions` (editable): `1st Revision Req`, `1st Revision Completed`, `Permit 1st Resubmitted`, `2nd Revision Req`, `2nd Revision Completed`, `Permit 2nd Resubmitted`.
  - Sección `Approval` (editable): `Runner Pick up`, `Permit #`, `Permit Approved`, `Permit Expires`, `Permit Fee`.
  - Sección `Status` (editable): `Permit Status`.
- VK-36: panel de detalle de un proyecto `KMV-Miscellaneous` (filas de la maestra): `Project Status`, `LT` editables; `Project Name`, `Customer`, `Date Received` y `Obs` de sólo lectura.

## 4. MOT y paquetes: `KMV 2.0 | MOT & Packages`

Reporte: `KMV 2.0 | MOT & Packages` (filas `MOT` por cada hija `KMV-MOT` y `Package` por cada proyecto con `Prepare Packages`).

- VK-40: `Restrict by`: `Permitting Team`.
- VK-41: tabla: `Tracking Project`, `Row Type`, `Agency`, `MOT Status`, `Project Name`, `Design MOT Request`, `Prepare Packages Request`, `Submitted Date`.
- VK-42: filtros guardados: `Open` (`MOT Status` no es `COMPLETE` ni `CANCELLED`), `MOT`, `Packages`, `All`.
- VK-43: vista de tarjetas por `MOT Status`.
- VK-44: sin formulario de filas nuevas.
- VK-45: panel de detalle:
  - Sección `Project` (sólo lectura): `Tracking Project`, `Row Type`, `Agency`, `Customer`, `Project Name`, `Project Address`, `City`, `Designers`, `Date Received`, `PM Approval Date`.
  - Sección `Packages` (editable; filas `Package`): `Prepare Packages Request`, `Prepare Packages QC`, `Prepare Packages Completed`.
  - Sección `MOT Design` (editable; filas `MOT`): `Design MOT Request`, `Design MOT QC`, `Design MOT Completed`, `Custom MOT`, `TYPICAL MOT`.
  - Sección `MOT Permit` (editable; filas `MOT`): `LT`, `Submitted Date`, `Permit #`, `1st Revision Req`, `1st Revision Completed`, `Permit 1st Resubmitted`, `Permit Approved`, `Permit Expires`.
  - Sección `Status` (editable): `MOT Status`.
  - Con condición de panel: uno para `Row Type` `Package` y otro para `MOT`.

## 5. Records: `KMV 2.0 | Records`

- VK-50: `Restrict by`: `Records Owner`.
- VK-51: tabla: `Tracking Project`, `Project Name`, `Agency`, `Records Status`, `Record Request`, `Reminder Sent`, `Record Received`.
- VK-52: filtros guardados: `Open` (`Records Status` vacío, `Not Received` o `Ticket - coordination`), `All`.
- VK-53: sin formulario de filas nuevas (las pide la coordinación con `Records Needed` o `Records Owner`).
- VK-54: panel de detalle: sección `Project` (sólo lectura: `Tracking Project`, `Customer`, `Agency`, `Project Name`, `Project Address`, `City`, `County`, `Date Received`); sección `Request` (editable: `Request Type`, `Send Method`, `Record Request`, `Reminder Sent`, `LT Records`, `PRR #`, `Future Project #`, `Security Key`); sección `Result` (editable: `Record Received`, `Records Status`, `Record Box`).

## 6. Facturación: `KMV 2.0 | Billing`

- VK-60: sin `Restrict by` (la ve sólo la persona de facturación).
- VK-61: tabla: `Tracking Project`, `Row Type`, `Customer`, `Project Name`, `Invoice Status`, `Purchase Orden`, `Invoice Sent`, `Invoice Paid`.
- VK-62: filtros guardados: `To invoice` (`Invoice? GALP` sin marcar y `PM Approval Date` con fecha, como los `Generator`), `Sent` (`Invoice Status` es `SENT TO CUSTOMER`), `All`.
- VK-63: sin formulario de filas nuevas.
- VK-64: panel de detalle: sección `Project` (sólo lectura: `Tracking Project`, `Type of Project`, `Customer`, `Project Name`, `Project Address`, `County`, `Agency`, `Contractor`, `Construction Manager`, `PM Approval Date`, `Project Status`); sección `Quantities` (sólo lectura: metraje, `Custom MOT`, `TYPICAL MOT`, `Additional Site Survey`, `Survey Certified`, `Tone Locating`, `Sonde FTG`, `GPR`, `Permit #`, `Permit Fee`, `Stamp And Signatures #`); sección `Invoice` (editable: `Purchase Orden`, `Invoice? GALP`, `Invoice? KMV`, `Customer invoice?`, `Invoice Completed (Galp)`, `PM Approval Invoice Date`, `Invoice Sent`, `Invoice Paid`); `Invoice Status` de sólo lectura.

## Cómo probar una vista nueva

- VK-70: abrir la vista con otra cuenta o en modo de vista previa y revisar que la persona vea sólo lo suyo (`Restrict by`).
- VK-71: en la de coordinación, crear un proyecto y esperar su número; luego crear un permiso con ese `Parent Project` y `Agency`: en un minuto queda bajo el proyecto y aparece en `KMV 2.0 | Permits`.
- VK-72: en la de permisos, cambiar `Permit Status`: en un minuto se ve en la vista de coordinación como `Project Status` de esa fila.
