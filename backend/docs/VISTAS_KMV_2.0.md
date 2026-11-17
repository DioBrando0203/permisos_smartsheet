# Vistas (Dynamic View) de la versión 2.0

Guía para armar las vistas de cada equipo. Los nombres de pestañas y opciones son los de la pantalla de configuración de Dynamic View (`Settings`). Regla única (decisión del usuario, 2026-11-17 15:21, lo más cómodo y limpio): cada vista va directo sobre su hoja; sólo la del equipo de permisos va sobre su reporte, porque junta dos hojas. Reglas del servicio en SPEC-B20 y PEN-54.

## Dónde va cada vista

- VK-00a: `PROJECT KMV 2.0 - PROJECTS` (coordinación, crea proyectos): hoja `PROJECT KMV 2.0 (Prototype)` con el filtro compartido `Projects`.
- VK-00b: `PROJECT KMV 2.0 - PERMITS` (coordinación, crea trámites): hoja `PROJECT KMV 2.0 (Prototype)` con el filtro compartido `Permits`.
- VK-00c: `PROJECT KMV 2.0 - DESIGN` (diseño): hoja `PROJECT KMV 2.0 (Prototype)` con el filtro compartido `Projects`, restringida por `Designers`.
- VK-00d: `PROJECT KMV 2.0 - PERMITS TEAM` (equipo de permisos): reporte `KMV 2.0 | Permits` (sus permisos y sus proyectos `KMV-Miscellaneous`), restringida por `Permitting Team`. Es la única sobre un reporte; agregar `Revision Stage` al reporte desde la interfaz.
- VK-00e: `PROJECT KMV 2.0 - MOT & PACKAGES`: hoja `MOT & Packages (Prototype)`, restringida por `Permitting Team`.
- VK-00f: `PROJECT KMV 2.0 - RECORDS`: hoja `Records Requests (Prototype)`, restringida por `Records Owner`.
- VK-00g: `PROJECT KMV 2.0 - BILLING`: hoja `Billing (Prototype)`, sin restricción.
- VK-00h: `PROJECT KMV 2.0 - DESIGN TICKETS` (si se queda la hoja): hoja `Design Tickets (Prototype)`, restringida por `DT Owner`.
- VK-00i: sobre una hoja, la vista ve al instante cualquier columna nueva; sobre un reporte, cada columna nueva hay que agregarla al reporte a mano (la API no edita reportes).

## Por qué casi todas van sobre su hoja

- VK-00j: cada hoja de equipo (`Permits`, `MOT & Packages`, `Records Requests`, `Billing`, `Design Tickets`) ya trae copiados los datos de su proyecto desde la maestra (`Tracking Project`, `Customer`, `Project Name`, `Project Address`, `City`, `Designers`, `Date Received`, etc.). Los copia el servicio, siempre al día y bloqueados. Por eso una vista sobre la hoja ya muestra en una fila el proyecto y el trabajo del equipo: no hace falta un reporte para traer columnas de la maestra.
- VK-00k: la coordinación y diseño trabajan sobre la maestra misma, que tiene todas sus columnas.
- VK-00l: un reporte sólo hace falta cuando una vista debe mostrar filas de dos hojas. Pasa una vez: el equipo de permisos ve sus permisos (hoja `Permits`) y sus proyectos `KMV-Miscellaneous` (filas de la maestra), así que su vista va sobre el reporte `KMV 2.0 | Permits`.
- VK-00m: si a un equipo le falta una columna de la maestra (por ejemplo `Project Status` del proyecto en `MOT & Packages`), no se arma un reporte: se pide que el servicio la agregue a lo que copia en esa hoja.

## Para continuar (en orden)

- VK-00n: reiniciar el backend si no se hizo después del último cambio de código.
- VK-00o: en la maestra `PROJECT KMV 2.0 (Prototype)`, crear dos filtros compartidos (VK-01b): `Projects` (`Type of Project` `is one of` `KMV-P`, `KMV-Miscellaneous`) y `Permits` (`Type of Project` `is one of` `KMV-Permit`, `KMV-Line`, `KMV-MOT`), sin `Include parent rows`.
- VK-00p: en el reporte `KMV 2.0 | Permits`, agregar la columna `Revision Stage` (botón de columnas, guardar).
- VK-00q: armar las vistas en el orden de la lista de arriba (VK-00a a VK-00h), siguiendo cada sección de esta guía.
- VK-00r: en `Permits` y `MOT & Packages`, formato condicional: `Permit Status` o `MOT Status` = `CANCELLED` → gris y tachado.
- VK-00s: probar el flujo (VK-45 a VK-48).

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
- VK-09b: `Obs` nunca se edita (decisión del usuario): las notas se escriben como conversación de la fila (pestaña `Comments` del panel) y el servicio las copia a `Obs` (SPEC-B17). En toda vista `Obs` va de sólo lectura (`Read-Only`) y en `View Display` quedan marcados `Display comments` y `Users can add comments`.
- VK-10: ordenar la tabla por `Tracking Project` de mayor a menor (lo nuevo arriba) y, ya en la vista, guardar un filtro `Open` con lo pendiente.

## 1. Coordinación (Zaira): dos vistas sobre la maestra

Origen de las dos: la hoja `PROJECT KMV 2.0 (Prototype)`. Una vista para proyectos y otra para trámites: cada panel queda corto.

### 1A. `PROJECT KMV 2.0 - PROJECTS`

- VK-11: en la maestra, filtro compartido `Projects`: `Type of Project` `is one of` `KMV-P`, `KMV-Miscellaneous` (VK-01b). `General`: `Restrict view by current user` sin restricción; `Restrict view by sheet filter` = `Projects`; `New Item Submission` = `Allow`.
- VK-12: `View Display` > `Visible fields`, en este orden: `Tracking Project`, `Type of Project`, `Customer`, `Project Name`, `Project Status`, `Date Received`, `Drawing Due Date`, `Designers`, `Permitting Team`.
- VK-13: `Details Panel`, en este orden:
  - Para crear (obligatorios): `Type of Project`, `Customer`, `Date Received`, `Project Name`.
  - Datos del proyecto: `Project Address`, `City`, `County`, `Task`, `Priority`, `CC System`, `Drawing Due Date`, `Linked Tracking`.
  - Asignación: `Designers`, `Permitting Team`, `Surveyor`, `Engineer`, `Prepare Packages`, `DT Owner`, `Construction Manager`, `Contractor`. Records no va aquí: se pide en la fila del trámite, que tiene la agencia (VK-18).
  - Avance: `Project Status`, `Survey Completed`, `Design Completed`, `PM Approval Date`, `LT`.
  - Sólo lectura: `Tracking Project`, `Design Ticket` y `Mile Post` (los llena el `DT Owner` en su hoja, sección 7), `Invoice Status`, `Obs`.
  - `Details panel description`: "The project number appears about a minute after saving (Pending ID until then)."
- VK-14: `Field Logic` (opcional), regla `Design`: when `Type of Project` `is one of` `KMV-P` → mostrar `Design Ticket`, `Mile Post` y `DT Owner` (en 2026 casi nunca se usaron en `KMV-Miscellaneous`: 4 de 425). Lo demás siempre visible, en el orden de VK-13. Quitar del panel `Control Linked Tracking` (VK-09).
- VK-15: `Sharing`: la coordinación.

### 1B. `PROJECT KMV 2.0 - PERMITS`

- VK-16: en la maestra, filtro compartido `Permits`: `Type of Project` `is one of` `KMV-Permit`, `KMV-Line`, `KMV-MOT` (VK-01b). `General`: sin restricción por usuario; `Restrict view by sheet filter` = `Permits`; `New Item Submission` = `Allow`. Ojo: una fila nueva sin tipo no cumple el filtro; `Type of Project` es lo primero y obligatorio.
- VK-17: `View Display` > `Visible fields`: `Tracking Project`, `Parent Project`, `Type of Project`, `Agency`, `Project Status`, `Permitting Team`, `Project Name`.
- VK-18: `Details Panel`, en este orden:
  - Para crear (obligatorios): `Type of Project`, `Parent Project`, `Agency`.
  - Opcionales: `Permitting Team` (vacío = el del proyecto), `Contractor`, `Records Needed` y `Records Owner` (Records de esta agencia: la fila de Records se crea sola, siempre que haya `Agency`), `Project Status` (sólo si nace `NO PERMIT REQUIRED`, o para cancelar con `CANCELLED`).
  - Sólo lectura: `Tracking Project`, `Project Name`, `Permit #`, `Permit Approved`, `Permit Expires`.
  - `Details panel description`: "Choose the project in Parent Project. In about a minute the row moves under it and goes to the team sheet."
- VK-19: sin `Field Logic`: el panel es corto; lo de sólo lectura queda abajo y se llena solo cuando la fila ya está bajo su proyecto.
- VK-20: `Sharing`: la coordinación.

## 2. Diseño: `PROJECT KMV 2.0 - DESIGN`

Origen: la hoja `PROJECT KMV 2.0 (Prototype)` (una fila por proyecto). El metraje se llena aquí; facturación lo ve en `Billing`, bloqueado.

- VK-21: `General`: `Restrict view by current user` = `Designers`; `Restrict view by sheet filter` = `Projects`; `New Item Submission` = `Do Not Allow`.
- VK-22: `Visible fields`: `Tracking Project`, `Project Name`, `Customer`, `Project Status`, `Records Status`, `Drawing Due Date`, `QC IN`, `QC OUT`, `Design Completed`, `Total Footage`. `Records Status` dice si ya llegaron los Records del proyecto: `Received`, `No records` o `Pending (1/2 received)`; vacío si no se pidieron.
- VK-23: `Details Panel`, en este orden:
  - Sólo lectura: `Tracking Project`, `Project Name`, `Customer`, `Type of Project`, `Date Received`, `Records Status`, `Design Ticket`, `Mile Post`.
  - Diseño (editable): `Project Status`, `Drawing Due Date`, `Survey Completed`, `QC IN`, `QC OUT`, `Design Completed`.
  - Metraje (editable): `Total Footage`, `UG`, `UG + Profile`, `ISP`, `Aerial`.
- VK-24: `Field Logic` (opcional), regla `Footage`: when `Type of Project` `is one of` `KMV-P` → mostrar `Total Footage`, `UG`, `UG + Profile`, `ISP`, `Aerial` (en `KMV-Miscellaneous` casi no hay diseño).
- VK-25: `Sharing`: el equipo de diseño.

## 3. Equipo de permisos: `PROJECT KMV 2.0 - PERMITS TEAM`

Origen: reporte `KMV 2.0 | Permits` (filas de `Permits` y los proyectos `KMV-Miscellaneous` del equipo). Antes de armarla, agregar `Revision Stage` al reporte (botón de columnas).

- VK-26: `General`: `Restrict view by current user` = `Permitting Team`; `New Item Submission` = `Do Not Allow` (las filas las crea el servicio desde la coordinación).
- VK-27: `Visible fields`: `Tracking Project`, `Type of Project`, `Agency`, `Permit Status`, `Revision Stage`, `Project Name`, `Submitted Date`, `Permit #`, `Permit Expires`.
- VK-28: `Details Panel`, en este orden (los títulos son sólo para ordenar; en Smartsheet se arrastran los campos):
  - Read-only: `Tracking Project`, `Type of Project`, `Agency`, `Customer`, `Project Name`, `Project Address`, `City`, `Design Ticket`, `Mile Post`, `Designers`, `Date Received`, `PM Approval Date`, `Revision Stage`.
  - Application: `LT`, `App Sent to Contractor`, `App Returned from Contractor`, `Submitted Date`, `Runner Submitting`.
  - 1st revision: `1st Revision Req`, `1st Revision Completed`, `Permit 1st Resubmitted`.
  - 2nd revision: `2nd Revision Req`, `2nd Revision Completed`, `Permit 2nd Resubmitted`.
  - Approval: `Runner Pick up`, `Permit #`, `Permit Approved`, `Permit Expires`, `Permit Fee`.
  - Status: `Permit Status`.
  - Para los proyectos `KMV-Miscellaneous`: `Project Status`, `LT` y `Obs` (sólo lectura: las notas van en `Comments`).
- VK-29: `Field Logic` (cuatro reglas; en cada una se eligen los campos a mostrar):
  - `Permit`: when `Type of Project` `is one of` `KMV-Permit`, `KMV-Line` → mostrar `LT`, `App Sent to Contractor`, `App Returned from Contractor`, `Submitted Date`, `Runner Submitting`, `Runner Pick up`, `Permit #`, `Permit Approved`, `Permit Expires`, `Permit Fee`, `Permit Status`.
  - `1st revision`: when `Revision Stage` `is one of` `1st Revision`, `2nd Revision` → mostrar `1st Revision Req`, `1st Revision Completed`, `Permit 1st Resubmitted`.
  - `2nd revision`: when `Revision Stage` `is one of` `2nd Revision` → mostrar `2nd Revision Req`, `2nd Revision Completed`, `Permit 2nd Resubmitted`.
  - `Project`: when `Type of Project` `is one of` `KMV-Miscellaneous` → mostrar `Project Status` y `Obs`.
  - `Revision Stage` la calcula la hoja (no se escribe): `1st Revision` cuando el permiso pasa a `4. Permit Needs Revision` o ya tiene `1st Revision Req`; `2nd Revision` cuando, ya reenviado (`Permit 1st Resubmitted`), vuelve a `4. Permit Needs Revision` o tiene `2nd Revision Req`; si no, `No revision`. Para que aparezca la primera revisión basta cambiar `Permit Status` a `4. Permit Needs Revision`.
- VK-30: `Sharing`: el equipo de permisos.

## 4. MOT y paquetes: `PROJECT KMV 2.0 - MOT & PACKAGES`

Origen: la hoja `MOT & Packages (Prototype)` (filas `MOT` y `Package`).

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

## 5. Records: `PROJECT KMV 2.0 - RECORDS`

Origen: la hoja `Records Requests (Prototype)`.

- VK-36: `General`: `Restrict view by current user` = `Records Owner`; `New Item Submission` = `Do Not Allow` (las pide la coordinación con `Records Needed` o `Records Owner` en la fila del permiso, con `Agency`).
- VK-37: `Visible fields`: `Tracking Project`, `Project Name`, `Agency`, `Records Status`, `Record Request`, `Reminder Sent`, `Record Received`.
- VK-38: `Details Panel`: sólo lectura `Tracking Project`, `Customer`, `Agency`, `Project Name`, `Project Address`, `City`, `County`, `Date Received`; editables `Request Type`, `Send Method`, `Record Request`, `Reminder Sent`, `LT Records`, `PRR #`, `Future Project #`, `Security Key`, `Record Received`, `Records Status`, `Record Box`.
- VK-39: `Field Logic`: `PRR #` y `Security Key` sólo cuando `Request Type` es `PRR`; `Future Project #` sólo cuando es `Future Project`.
- VK-40: `Sharing`: el equipo de Records.

## 6. Facturación: `PROJECT KMV 2.0 - BILLING`

Origen: la hoja `Billing (Prototype)`.

- VK-41: `General`: sin restricción por usuario; `New Item Submission` = `Do Not Allow`.
- VK-42: `Visible fields`: `Tracking Project`, `Row Type`, `Customer`, `Project Name`, `Invoice Status`, `Purchase Orden`, `Invoice Sent`, `Invoice Paid`.
- VK-43: `Details Panel`: sólo lectura `Tracking Project`, `Type of Project`, `Customer`, `Project Name`, `Project Address`, `County`, `Agency`, `Contractor`, `Construction Manager`, `PM Approval Date`, `Project Status`, el metraje, `Custom MOT`, `TYPICAL MOT`, `Additional Site Survey`, `Survey Certified`, `Tone Locating`, `Sonde FTG`, `GPR`, `Permit #`, `Permit Fee`, `Stamp And Signatures #`; editables `Purchase Orden`, `Invoice? GALP`, `Invoice? KMV`, `Customer invoice?`, `Invoice Completed (Galp)`, `PM Approval Invoice Date`, `Invoice Sent`, `Invoice Paid`; sólo lectura `Invoice Status`.
- VK-44: `Sharing`: sólo la persona de facturación.

## 7. Design Ticket y Mile Post: `PROJECT KMV 2.0 - DESIGN TICKETS`

Origen: la hoja `Design Tickets (Prototype)` (una fila por proyecto con `DT Owner`, la crea el servicio).

- VK-50: `General`: `Restrict view by current user` = `DT Owner`; `New Item Submission` = `Do Not Allow` (la fila sale al asignar `DT Owner` en el proyecto).
- VK-51: `Visible fields`: `Tracking Project`, `Project Name`, `Customer`, `City`, `Design Ticket`, `Mile Post`, `Project Status`, `Date Received`.
- VK-52: `Details Panel`: editables `Design Ticket` y `Mile Post` (primero); sólo lectura `Tracking Project`, `Project Name`, `Customer`, `Project Address`, `City`, `County`, `Date Received`, `Designers`, `Project Status`. Lo que se escribe vuelve a la maestra y de allí a `Permits`.
- VK-53: `Sharing`: las personas que son `DT Owner`.

## Cómo probar una vista

- VK-45: guardar (`Save`) y abrir la vista (`Back to view`). Agregar una fila: el panel debe pedir sólo lo de crear.
- VK-46: en `PROJECTS`, crear un proyecto y esperar su número (aparece `Pending ID` y en un minuto el número).
- VK-47: en `PERMITS`, crear un permiso con ese número en `Parent Project` y una `Agency`: en un minuto queda bajo el proyecto y aparece en `PERMITS TEAM`.
- VK-48: en `PERMITS TEAM`, cambiar `Permit Status`: en un minuto se ve como `Project Status` de esa fila en la coordinación.
