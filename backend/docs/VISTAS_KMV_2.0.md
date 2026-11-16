# Vistas (Dynamic View) de la versión 2.0

Guía para armar las vistas de cada equipo. Los nombres de pestañas y opciones son los de la pantalla de configuración de Dynamic View (`Settings`). Las vistas de coordinación pueden ir directo sobre la maestra `PROJECT KMV 2.0 (Prototype)`; las de los equipos van sobre los reportes de `Pruebas/Producto/PROJECT KMV 2.0 - Prototype/Reports`. Reglas del servicio en SPEC-B20 y PEN-54.

## Dónde se configura cada cosa

- VK-01: `General`: `View name`, `Source sheet or report` (no se cambia después de crear la vista), `Restrict view by current user` (cada persona ve sólo las filas con su nombre en esa columna de contacto), `Restrict view by sheet filter` (qué filas existen en la vista: se elige un filtro compartido que ya existe en la hoja de origen, ver VK-01b), `New Item Submission` (`Allow` para poder agregar filas) y `Export to .csv file`.
- VK-01b: crear un filtro compartido en la hoja de origen (en la hoja, no en la vista): botón `Filter` > `New Filter`; condición sobre la columna (`is one of` = "es uno de", `is not one of` = "no es ninguno de"); ponerle nombre; marcar que se comparte (`Share filter`) y guardar. Después aparece en `Restrict view by sheet filter`. Si el origen es un reporte, el reporte ya trae su filtro y no hace falta.
- VK-02: `View Display` > `Displayed fields`: en `Available fields` marcas las columnas que se ven en la tabla; en `Visible fields` quedan en orden (se arrastran para ordenarlas). Ahí también `Attachments` y `Comments`.
- VK-03: `Details Panel`: los campos que aparecen al abrir una fila y también al agregar una fila nueva (el panel nuevo sale vacío). Se arrastran desde `Add Field` a `Details Panel Layout` en el orden en que se llenan. Al hacer clic en un campo del panel se marca de sólo lectura o obligatorio (`Required`), si la opción aparece. `Details panel description` sirve para un texto de ayuda arriba del panel. `Focus tab` en `Data`.
- VK-04: `Field Logic` (a la derecha del panel, `+ Logic`): muestra u oculta campos según el valor de otro. En `When` sólo aparecen columnas de lista desplegable (`Type of Project`, `Project Status`, `Priority`, `Task`, `Parent Project`, etc.); contactos (`Designers`, `Permitting Team`), texto y fechas no sirven de condición, aunque sí se pueden mostrar u ocultar. Úsala con `Type of Project` para que cada tipo de fila muestre sólo sus campos.
- VK-05: `Sharing`: quién entra a la vista. Lo que ve cada uno se limita en `General` > `Restrict view by current user`.

## Para que no canse la vista

- VK-06: `Visible fields` con 6 a 9 columnas, siempre en el mismo orden: ID y tipo, nombre, estado, la fecha que sigue y quién lo lleva. El resto va sólo al panel.
- VK-07: quitar `Primary` de `Visible fields` (siempre dice `KMV-P`) y poner primero `Tracking Project`.
- VK-08: en el panel, primero lo que se escribe al crear, luego lo que se va llenando con el trabajo y al final lo de sólo lectura. Lo que copia el servicio va de sólo lectura: si alguien lo cambia, el servicio lo vuelve a escribir.
- VK-09: nunca agregar columnas técnicas: `Master Row`, `Stable Tracking Project`, `Row Level`, `Row Order`, `Customer Code`, `Year`, `Control Linked Tracking`.
- VK-10: ordenar la tabla por `Tracking Project` de mayor a menor (lo nuevo arriba) y, ya en la vista, guardar un filtro `Open` con lo pendiente.

## 1. Coordinación (Zaira): dos vistas sobre la maestra

Origen de las dos: `PROJECT KMV 2.0 (Prototype)` (o el reporte `KMV 2.0 | Coordinator`). Una vista para proyectos y otra para permisos: cada panel queda corto.

### 1A. `PROJECT KMV 2.0 - PROJECTS`

- VK-11: en la maestra, filtro compartido `Projects`: `Type of Project` `is one of` `KMV-P`, `KMV-Miscellaneous` (VK-01b). `General`: `Restrict view by current user` sin restricción; `Restrict view by sheet filter` = `Projects`; `New Item Submission` = `Allow`.
- VK-12: `View Display` > `Visible fields`, en este orden: `Tracking Project`, `Type of Project`, `Customer`, `Project Name`, `Project Status`, `Date Received`, `Drawing Due Date`, `Designers`, `Permitting Team`.
- VK-13: `Details Panel`, en este orden:
  - Para crear (obligatorios): `Type of Project`, `Customer`, `Date Received`, `Project Name`.
  - Datos del proyecto: `Project Address`, `City`, `County`, `Task`, `Priority`, `CC System`, `Drawing Due Date`, `Linked Tracking`.
  - Asignación: `Designers`, `Permitting Team`, `Surveyor`, `Engineer`, `Prepare Packages`, `DT Owner`, `Construction Manager`, `Contractor`. Records no va aquí: se pide en la fila del permiso, que tiene la agencia (VK-18).
  - Avance: `Project Status`, `Survey Completed`, `Design Completed`, `PM Approval Date`, `LT`.
  - Sólo lectura: `Tracking Project`, `Design Ticket` y `Mile Post` (los llena el `DT Owner` en su hoja, sección 7), `Invoice Status`, `Obs`.
  - `Details panel description`: "The project number appears about a minute after saving (Pending ID until then)."
- VK-14: `Field Logic` (opcional), regla `Design`: when `Type of Project` `is one of` `KMV-P` → mostrar `Design Ticket`, `Mile Post` y `DT Owner` (en 2026 casi nunca se usaron en `KMV-Miscellaneous`: 4 de 425). Lo demás siempre visible, en el orden de VK-13. Quitar del panel `Control Linked Tracking` (VK-09).
- VK-15: `Sharing`: la coordinación.

### 1B. `PROJECT KMV 2.0 - PERMITS INTAKE`

- VK-16: en la maestra, filtro compartido `Permits`: `Type of Project` `is one of` `KMV-Permit`, `KMV-Line`, `KMV-MOT` (VK-01b). `General`: sin restricción por usuario; `Restrict view by sheet filter` = `Permits`; `New Item Submission` = `Allow`. Ojo: una fila nueva sin tipo no cumple el filtro; `Type of Project` es lo primero y obligatorio.
- VK-17: `View Display` > `Visible fields`: `Tracking Project`, `Parent Project`, `Type of Project`, `Agency`, `Project Status`, `Permitting Team`, `Project Name`.
- VK-18: `Details Panel`, en este orden:
  - Para crear (obligatorios): `Type of Project`, `Parent Project`, `Agency`.
  - Opcionales: `Permitting Team` (vacío = el del proyecto), `Contractor`, `Records Needed` y `Records Owner` (Records de esta agencia: la fila de Records se crea sola, siempre que haya `Agency`), `Project Status` (sólo si nace `NO PERMIT REQUIRED`, o para cancelar con `CANCELLED`).
  - Sólo lectura: `Tracking Project`, `Project Name`, `Permit #`, `Permit Approved`, `Permit Expires`.
  - `Details panel description`: "Choose the project in Parent Project. In about a minute the row moves under it and goes to the team sheet."
- VK-19: sin `Field Logic`: el panel es corto; lo de sólo lectura queda abajo y se llena solo cuando la fila ya está bajo su proyecto.
- VK-20: `Sharing`: la coordinación.

## 2. Diseño: `KMV 2.0 | Design Projects`

Origen: reporte `KMV 2.0 | Design Projects` (sólo la maestra: una fila por proyecto `KMV-P` o `KMV-Miscellaneous`). El metraje se llena aquí; facturación lo ve en `Billing`, bloqueado.

- VK-21: `General`: `Restrict view by current user` = `Designers`; `New Item Submission` = `Do Not Allow`.
- VK-22: `Visible fields`: `Tracking Project`, `Project Name`, `Customer`, `Project Status`, `Drawing Due Date`, `QC IN`, `QC OUT`, `Design Completed`, `Total Footage`.
- VK-23: `Details Panel`, en este orden:
  - Sólo lectura: `Tracking Project`, `Project Name`, `Customer`, `Type of Project`, `Date Received`, `Design Ticket`, `Mile Post`.
  - Diseño (editable): `Project Status`, `Drawing Due Date`, `Survey Completed`, `QC IN`, `QC OUT`, `Design Completed`.
  - Metraje (editable): `Total Footage`, `UG`, `UG + Profile`, `ISP`, `Aerial`.
- VK-24: `Field Logic` (opcional), regla `Design`: when `Type of Project` `is one of` `KMV-P` → mostrar el metraje (en `KMV-Miscellaneous` casi no hay diseño).
- VK-25: `Sharing`: el equipo de diseño.

## 3. Permisos: `KMV 2.0 | Permits`

Origen: reporte `KMV 2.0 | Permits` (filas de `Permits` y los proyectos `KMV-Miscellaneous` del equipo).

- VK-26: `General`: `Restrict view by current user` = `Permitting Team`; `New Item Submission` = `Do Not Allow` (las filas las crea el servicio desde la coordinación).
- VK-27: `Visible fields`: `Tracking Project`, `Type of Project`, `Agency`, `Permit Status`, `Project Name`, `Submitted Date`, `Permit #`, `Permit Expires`.
- VK-28: `Details Panel`, en este orden:
  - Sólo lectura: `Tracking Project`, `Type of Project`, `Agency`, `Customer`, `Project Name`, `Project Address`, `City`, `Design Ticket`, `Mile Post`, `Designers`, `Date Received`, `PM Approval Date`.
  - Solicitud: `LT`, `App Sent to Contractor`, `App Returned from Contractor`, `Submitted Date`, `Runner Submitting`.
  - Revisiones: `1st Revision Req`, `1st Revision Completed`, `Permit 1st Resubmitted`, `2nd Revision Req`, `2nd Revision Completed`, `Permit 2nd Resubmitted`.
  - Aprobación: `Runner Pick up`, `Permit #`, `Permit Approved`, `Permit Expires`, `Permit Fee`.
  - Estado: `Permit Status`.
  - Para los proyectos `KMV-Miscellaneous`: `Project Status`, `LT`, `Obs`.
- VK-29: `Field Logic`: regla `Permit`: when `Type of Project` `is one of` `KMV-Permit`, `KMV-Line` → mostrar Solicitud, Revisiones, Aprobación y `Permit Status`; regla `Project`: when `Type of Project` `is one of` `KMV-Miscellaneous` → mostrar `Project Status` y `Obs`.
- VK-30: `Sharing`: el equipo de permisos.

## 4. MOT y paquetes: `KMV 2.0 | MOT & Packages`

Origen: reporte `KMV 2.0 | MOT & Packages` (filas `MOT` y `Package`).

- VK-31: `General`: `Restrict view by current user` = `Permitting Team`; `New Item Submission` = `Do Not Allow`.
- VK-32: `Visible fields`: `Tracking Project`, `Row Type`, `Agency`, `MOT Status`, `Project Name`, `Design MOT Request`, `Prepare Packages Request`, `Submitted Date`.
- VK-33: `Details Panel`, en este orden:
  - Sólo lectura: `Tracking Project`, `Row Type`, `Agency`, `Customer`, `Project Name`, `Project Address`, `City`, `Designers`, `Date Received`, `PM Approval Date`.
  - Paquetes: `Prepare Packages Request`, `Prepare Packages QC`, `Prepare Packages Completed`.
  - Diseño de MOT: `Design MOT Request`, `Design MOT QC`, `Design MOT Completed`, `Custom MOT`, `TYPICAL MOT`.
  - Permiso de MOT: `LT`, `Submitted Date`, `Permit #`, `1st Revision Req`, `1st Revision Completed`, `Permit 1st Resubmitted`, `Permit Approved`, `Permit Expires`.
  - Estado: `MOT Status`.
- VK-34: `Field Logic` por `Row Type` (Paquetes cuando es `Package`; Diseño y Permiso de MOT cuando es `MOT`) sólo si `Row Type` es lista desplegable en `MOT & Packages (Prototype)`; hoy es texto, así que todo queda visible en el orden de VK-33.
- VK-35: `Sharing`: la persona de MOT.

## 5. Records: `KMV 2.0 | Records`

- VK-36: `General`: `Restrict view by current user` = `Records Owner`; `New Item Submission` = `Do Not Allow` (las pide la coordinación con `Records Needed` o `Records Owner` en la fila del permiso, con `Agency`).
- VK-37: `Visible fields`: `Tracking Project`, `Project Name`, `Agency`, `Records Status`, `Record Request`, `Reminder Sent`, `Record Received`.
- VK-38: `Details Panel`: sólo lectura `Tracking Project`, `Customer`, `Agency`, `Project Name`, `Project Address`, `City`, `County`, `Date Received`; editables `Request Type`, `Send Method`, `Record Request`, `Reminder Sent`, `LT Records`, `PRR #`, `Future Project #`, `Security Key`, `Record Received`, `Records Status`, `Record Box`.
- VK-39: `Field Logic`: `PRR #` y `Security Key` sólo cuando `Request Type` es `PRR`; `Future Project #` sólo cuando es `Future Project`.
- VK-40: `Sharing`: el equipo de Records.

## 6. Facturación: `KMV 2.0 | Billing`

- VK-41: `General`: sin restricción por usuario; `New Item Submission` = `Do Not Allow`.
- VK-42: `Visible fields`: `Tracking Project`, `Row Type`, `Customer`, `Project Name`, `Invoice Status`, `Purchase Orden`, `Invoice Sent`, `Invoice Paid`.
- VK-43: `Details Panel`: sólo lectura `Tracking Project`, `Type of Project`, `Customer`, `Project Name`, `Project Address`, `County`, `Agency`, `Contractor`, `Construction Manager`, `PM Approval Date`, `Project Status`, el metraje, `Custom MOT`, `TYPICAL MOT`, `Additional Site Survey`, `Survey Certified`, `Tone Locating`, `Sonde FTG`, `GPR`, `Permit #`, `Permit Fee`, `Stamp And Signatures #`; editables `Purchase Orden`, `Invoice? GALP`, `Invoice? KMV`, `Customer invoice?`, `Invoice Completed (Galp)`, `PM Approval Invoice Date`, `Invoice Sent`, `Invoice Paid`; sólo lectura `Invoice Status`.
- VK-44: `Sharing`: sólo la persona de facturación.

## 7. Design Ticket y Mile Post: `KMV 2.0 | Design Tickets`

Origen: reporte `KMV 2.0 | Design Tickets` (hoja `Design Tickets (Prototype)`: una fila por proyecto con `DT Owner`, la crea el servicio).

- VK-50: `General`: `Restrict view by current user` = `DT Owner`; `New Item Submission` = `Do Not Allow` (la fila sale al asignar `DT Owner` en el proyecto).
- VK-51: `Visible fields`: `Tracking Project`, `Project Name`, `Customer`, `City`, `Design Ticket`, `Mile Post`, `Project Status`, `Date Received`.
- VK-52: `Details Panel`: editables `Design Ticket` y `Mile Post` (primero); sólo lectura `Tracking Project`, `Project Name`, `Customer`, `Project Address`, `City`, `County`, `Date Received`, `Designers`, `Project Status`. Lo que se escribe vuelve a la maestra y de allí a `Permits`.
- VK-53: `Sharing`: las personas que son `DT Owner`.

## Cómo probar una vista

- VK-45: guardar (`Save`) y abrir la vista (`Back to view`). Agregar una fila: el panel debe pedir sólo lo de crear.
- VK-46: en `PROJECTS`, crear un proyecto y esperar su número (aparece `Pending ID` y en un minuto el número).
- VK-47: en `PERMITS INTAKE`, crear un permiso con ese número en `Parent Project` y una `Agency`: en un minuto queda bajo el proyecto y aparece en `KMV 2.0 | Permits`.
- VK-48: en `KMV 2.0 | Permits`, cambiar `Permit Status`: en un minuto se ve como `Project Status` de esa fila en la coordinación.
