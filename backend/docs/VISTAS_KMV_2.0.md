# Vistas (Dynamic View) de la versión 2.0

Guía para armar las vistas de cada equipo. Los nombres de pestañas y opciones son los de la pantalla de configuración de Dynamic View (`Settings`). Regla única (decisión del usuario, 2026-11-17 15:27): todas las vistas van directo sobre su hoja; no se usa ningún reporte. Reglas del servicio en SPEC-B20 y PEN-54.

## Dónde va cada vista

- VK-00a: `PROJECT KMV 2.0 - PROJECTS` (coordinación, crea proyectos): hoja `PROJECT KMV 2.0 (Prototype)` con el filtro compartido `Projects`.
- VK-00b: `PROJECT KMV 2.0 - PERMITS` (coordinación, crea trámites): hoja `PROJECT KMV 2.0 (Prototype)` con el filtro compartido `Permits`.
- VK-00c: `PROJECT KMV 2.0 - DESIGN` (diseño): hoja `PROJECT KMV 2.0 (Prototype)` con el filtro compartido `Projects`, restringida por `Designers`.
- VK-00d: `PROJECT KMV 2.0 - PERMITS TEAM` (equipo de permisos): hoja `Permits (Prototype)`, restringida por `Permitting Team`. Trae sus permisos y líneas y también sus proyectos `KMV-Miscellaneous` (HP-16): todo en una vista.
- VK-00d3: `Linked Tracking` (proyecto anterior relacionado) va en todas las vistas, junto a `Tracking Project`: todas las hojas de equipo lo traen copiado de su proyecto (decisión del usuario: dato de seguimiento que siempre debe estar).
- VK-00e: `PROJECT KMV 2.0 - MOT & PACKAGES`: hoja `MOT & Packages (Prototype)`, sin restricción por usuario: paquetes y MOT los hace una sola persona para todos los proyectos (historial 2026, K2-85c).
- VK-00f: `PROJECT KMV 2.0 - RECORDS`: hoja `Records Requests (Prototype)`, restringida por `Records Owner`.
- VK-00g: `PROJECT KMV 2.0 - BILLING`: hoja `Billing (Prototype)`, sin restricción.
- VK-00h: `PROJECT KMV 2.0 - DESIGN TICKETS` (si se queda la hoja): hoja `Design Tickets (Prototype)`, restringida por `DT Owner`.
- VK-00i: sobre una hoja, la vista ve al instante cualquier columna nueva; sobre un reporte habría que agregarla al reporte a mano (la API no edita reportes). Por eso ninguna vista usa reporte.

## Por qué casi todas van sobre su hoja

- VK-00j: cada hoja de equipo (`Permits`, `MOT & Packages`, `Records Requests`, `Billing`, `Design Tickets`) ya trae copiados los datos de su proyecto desde la maestra (`Tracking Project`, `Customer`, `Project Name`, `Project Address`, `City`, `Designers`, `Date Received`, etc.). Los copia el servicio, siempre al día y bloqueados. Por eso una vista sobre la hoja ya muestra en una fila el proyecto y el trabajo del equipo: no hace falta un reporte para traer columnas de la maestra.
- VK-00k: la coordinación y diseño trabajan sobre la maestra misma, que tiene todas sus columnas.
- VK-00l: un reporte sólo haría falta para mostrar filas de dos hojas en una misma vista. El único caso era el equipo de permisos (sus permisos y sus proyectos `KMV-Miscellaneous`); se resolvió llevando esos proyectos también a la hoja `Permits` (decisión del usuario: aunque se usen poco, deben estar en su hoja).
- VK-00m: si a un equipo le falta una columna de la maestra (por ejemplo `Project Status` del proyecto en `MOT & Packages`), no se arma un reporte: se pide que el servicio la agregue a lo que copia en esa hoja.

## Avance (2026-11-17 15:44)

- VK-00t: hecho: backend reiniciado con el último código (15:37; comprobado: el proyecto `KMV-26-0002` ya tiene su fila en `Permits` y `Linked Tracking` se copia, por ejemplo en `Billing` de `KMV-26-0005`). Vistas armadas por el usuario: `PROJECTS` y `PERMITS` (coordinación, sobre la maestra) y `PERMITS TEAM` (sobre la hoja `Permits`, con `Linked Tracking`).
- VK-00t2 (2026-11-17 15:51, revisado en capturas): `PROJECTS` (6 proyectos, filtro `Projects`) y `PERMITS` (9 trámites, filtro `Permits`) funcionan, con `Linked Tracking`. La vista de diseño quedó armada sobre el reporte `KMV 2.0 | Design Projects` (no sobre la maestra): se deja así; falta agregar al reporte `Records Status` y `Linked Tracking` (botón de columnas, desde la interfaz) y luego en la vista: en `Visible fields` y en el panel de sólo lectura, con `Tracking Project`, `Project Name` y `Customer` arriba del panel.
- VK-00t3 (2026-11-17 18:21): `MOT & PACKAGES` armada hasta VK-35b. Corregir en ella: `General` > `Restrict view by current user` sin restricción (VK-31) y `Sharing` (VK-35); en `PERMITS` (coordinación), sumar `Prepare Packages` a los opcionales del panel (VK-18); automatizaciones 1 y 2 de VK-35b (la 3 es opcional).
- VK-00t4 (2026-11-22 16:53): revisión de las vistas con Playwright (cuenta dueña) y correcciones pedidas por el usuario.
  - Ya estaba bien: restricción por usuario en `Permits (Prototype)` (`Permitting Team`), `Records Requests (Prototype)` (`Records Owner`) y `KMV 2.0 | Design Projects` (`Designers`); `MOT & Packages (Prototype)` coincide con VK-31 a VK-34.
  - Corregido en `Records Requests (Prototype)`: las dos reglas de `Field Logic` pasaron de `Show the following fields as Read-only` a `Editable` (`PRR #`, `Future Project #`) y `Security Key` se sumó a la regla de `PRR` (VK-39).
  - Corregido en `Permits (Prototype)` (`PERMITS TEAM`): `Permit Status` en `Visible fields`, en el puesto 5 después de `Agency` (VK-27); la regla `Permit` incluye `KMV-Miscellaneous` (VK-29). Queda una regla vieja `Project` (`KMV-Miscellaneous` → `Permit Status`) que ahora sobra y no estorba.
  - Corregido: obligatorios (`Require`) en `PROJECTS` (`Type of Project`, `Customer`, `Date Received`, `Project Name`, VK-13) y en `PERMITS` (`Type of Project`, `Parent Project`, `Agency`, VK-18).
  - Falta, sin tocar: `Sharing` de `PROJECTS`, `PERMITS`, `PERMITS TEAM` y diseño (sólo la ve el dueño); en diseño, `Users can add comments` (VK-09b, el usuario lo deja para después); en `PERMITS TEAM`, el bloque de sólo lectura del panel (VK-28), y la tabla tiene además `Customer`, `Project Address`, `City`, `Designers`, `Date Received`, `PM Approval Date`, con `Revision Stage` al final; en Records, el bloque de sólo lectura y `Reminder Sent` en el panel (VK-38) y `Reminder Sent` en la tabla (VK-37); en `PROJECTS`, quitar del panel `Control Linked Tracking`, `Records Needed` y `Records Owner`, y dejar `Design Ticket` y `Mile Post` de sólo lectura (VK-13, VK-14); en `PERMITS`, `Prepare Packages` en el panel (VK-18); vistas `BILLING`, `DESIGN TICKETS` y de clientes (K2-87b); automatizaciones de `MOT & Packages`, Records y `Billing` (hoy 0); la vista vacía `KMV 2.0 | Records` sobra; tres vistas conservan el nombre de su hoja.
- VK-00u: hecho (2026-11-17 15:48): filtros compartidos `Projects` y `Permits` creados en la maestra (además del `Open` que venía de la 1.0). Falta: elegirlos en `General` > `Restrict view by sheet filter` de `PROJECTS`, `PERMITS` y `DESIGN`; vistas `DESIGN`, `MOT & PACKAGES`, `RECORDS`, `BILLING` (y `DESIGN TICKETS` si se queda); tachado de `CANCELLED` en `Permits` y `MOT & Packages`; probar el flujo (VK-45 a VK-48).
- VK-00t5 (2026-11-22 21:50, pedido del usuario: agregar lo que falta en la 2.0): hecho con la aplicación de Dynamic View (el mismo pedido que manda la pantalla al guardar, releído después).
  - Nombres: `PROJECT KMV 2.0 - PERMITS TEAM`, `PROJECT KMV 2.0 - MOT & PACKAGES`, `PROJECT KMV 2.0 - RECORDS` y `PROJECT KMV 2.0 - DESIGN` (antes con el nombre de su hoja o reporte; los enlaces no cambian porque van por id).
  - `PERMITS TEAM`: tabla como VK-27 (10 columnas) y panel como VK-28, con el bloque de sólo lectura arriba; las cuatro reglas de `Field Logic` intactas.
  - `RECORDS`: panel como VK-38 (sólo lectura arriba, `Reminder Sent` agregado) y `Reminder Sent` en la tabla (VK-37); reglas VK-39 intactas.
  - `PROJECTS`: panel como VK-13 (fuera `Control Linked Tracking`, `Records Needed` y `Records Owner`; agregados `Linked Tracking` y, de sólo lectura, `Tracking Project`, `Invoice Status` y `Obs`); la regla `Design` muestra `DT Owner` editable y `Design Ticket` y `Mile Post` de sólo lectura para `KMV-P`.
  - `PERMITS`: `Prepare Packages` en el panel y de sólo lectura `Tracking Project`, `Project Name`, `Permit #`, `Permit Approved` y `Permit Expires` (VK-18).
  - Vistas nuevas: `PROJECT KMV 2.0 - BILLING` (`9b0a278a-354e-4094-912a-86a3bebb0c6b`, VK-41 a VK-43), `PROJECT KMV 2.0 - DESIGN TICKETS` (`4ddedf77-4834-45af-9aef-7a7e9d45a712`, restringida por `DT Owner`, VK-50 a VK-52) y `PROJECT KMV 2.0 - CUSTOMERS` (`ea399e51-7048-4841-9721-45ae3b804769`, sobre la maestra, restringida por `Client Access`, sin filtro de hoja, sin panel de edición, comentarios visibles sin agregar, exportar permitido; tabla `Tracking Project`, `Project Name`, `Date Received`, `Permit Approved`, `Permit Expires`, `Project Status`, `Agency`, `Permit #`, `Obs`: `Submitted Date` no está en la maestra 2.0, queda en `Permits`). Comentarios y adjuntos visibles y editables en `BILLING` y `DESIGN TICKETS`; ninguna permite agregar filas.
  - Falta: `Sharing` de todas (a quién se comparte cada una lo decide el usuario); comentarios en la vista de diseño (VK-09b, en pausa); la vista vacía `KMV 2.0 | Records` y las de la 1.0 `KMV - Designers` y `KMV - CUSTOMERS` (ya no las enlaza ningún aviso de la 2.0) se borran cuando el usuario lo diga. Decisión del usuario (2026-11-22): no se borra ninguna vista de la 2.0, tampoco `KMV 2.0 | Records`.

## Para continuar (en orden)

- VK-00n: reiniciar el backend si no se hizo después del último cambio de código.
- VK-00o: en la maestra `PROJECT KMV 2.0 (Prototype)`, crear dos filtros compartidos (VK-01b), sin `Include parent rows`: `Projects` (`Type of Project` `is one of` `KMV-P`, `KMV-Miscellaneous`) y `Permits` (`KMV-Permit`, `KMV-Line`, `KMV-MOT`).
- VK-00q: armar las vistas en el orden de la lista de arriba (VK-00a a VK-00h), siguiendo cada sección de esta guía. `PERMITS TEAM` ya está armada sobre la hoja `Permits` (2026-11-17).
- VK-00r: hecho (2026-11-22): en `Permits` y `MOT & Packages`, `CANCELLED` deja la fila gris y tachada, con el resto de los colores de la maestra en todas las hojas (VK-60 a VK-65).
- VK-00s: probar el flujo (VK-45 a VK-48).
- VK-00v (2026-11-18): avisos de asignación en la 2.0: acción `Alert someone` > `Contacts in a cell` con la columna de asignación (`Designers`, `Permitting Team`, `Records Owner`, `DT Owner`); ya no hacen falta columnas `Email`. Quién aparece en esas columnas se maneja en `Contact List` (KMV_2.0 K2-89), apagado hasta completar el directorio. Las automatizaciones van en `Unrestricted` para que el aviso llegue también a correos personales (AUTOMATIZACIONES AU-00j).

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
- VK-12: `View Display` > `Visible fields`, en este orden: `Tracking Project`, `Linked Tracking`, `Type of Project`, `Customer`, `Project Name`, `Project Status`, `Date Received`, `Drawing Due Date`, `Designers`, `Permitting Team`.
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
- VK-17: `View Display` > `Visible fields`: `Tracking Project`, `Linked Tracking`, `Parent Project`, `Type of Project`, `Agency`, `Project Status`, `Permitting Team`, `Project Name`.
- VK-18: `Details Panel`, en este orden:
  - Para crear (obligatorios): `Type of Project`, `Parent Project`, `Agency`.
  - Opcionales: `Permitting Team` (vacío = el del proyecto), `Contractor`, `Records Needed` y `Records Owner` (Records de esta agencia: la fila de Records se crea sola, siempre que haya `Agency`), `Project Status` (sólo si nace `NO PERMIT REQUIRED`, o para cancelar con `CANCELLED`), `Prepare Packages` (sólo si este permiso lleva su propio paquete: crea su fila `Package` en `MOT & Packages`, HP-18).
  - Sólo lectura: `Tracking Project`, `Project Name`, `Permit #`, `Permit Approved`, `Permit Expires`.
  - `Details panel description`: "Choose the project in Parent Project. In about a minute the row moves under it and goes to the team sheet."
- VK-19: sin `Field Logic`: el panel es corto; lo de sólo lectura queda abajo y se llena solo cuando la fila ya está bajo su proyecto.
- VK-20: `Sharing`: la coordinación.

## 2. Diseño: `PROJECT KMV 2.0 - DESIGN`

Origen: la hoja `PROJECT KMV 2.0 (Prototype)` (una fila por proyecto). El metraje se llena aquí; facturación lo ve en `Billing`, bloqueado.

- VK-21: `General`: `Restrict view by current user` = `Designers`; `Restrict view by sheet filter` = `Projects`; `New Item Submission` = `Do Not Allow`.
- VK-22: `Visible fields`: `Tracking Project`, `Linked Tracking`, `Project Name`, `Customer`, `Project Status`, `Records Status`, `Drawing Due Date`, `QC IN`, `QC OUT`, `Design Completed`, `Total Footage`. `Records Status` dice si ya llegaron los Records del proyecto: `Received`, `No records` o `Pending (1/2 received)`; vacío si no se pidieron.
- VK-23: `Details Panel`, en este orden:
  - Sólo lectura: `Tracking Project`, `Project Name`, `Customer`, `Type of Project`, `Date Received`, `Records Status`, `Design Ticket`, `Mile Post`.
  - Diseño (editable): `Project Status`, `Drawing Due Date`, `Survey Completed`, `QC IN`, `QC OUT`, `Design Completed`.
  - Metraje (editable): `Total Footage`, `UG`, `UG + Profile`, `ISP`, `Aerial`.
- VK-24: `Field Logic` (opcional), regla `Footage`: when `Type of Project` `is one of` `KMV-P` → mostrar `Total Footage`, `UG`, `UG + Profile`, `ISP`, `Aerial` (en `KMV-Miscellaneous` casi no hay diseño).
- VK-25: `Sharing`: el equipo de diseño.

## 3. Equipo de permisos: `PROJECT KMV 2.0 - PERMITS TEAM`

Origen: la hoja `Permits (Prototype)`: sus permisos y líneas y sus proyectos `KMV-Miscellaneous` (una fila por proyecto; en esas filas `Type of Project` dice `KMV-Miscellaneous` y `Agency` puede estar vacía).

- VK-26: `General`: `Restrict view by current user` = `Permitting Team`; `New Item Submission` = `Do Not Allow` (las filas las crea el servicio desde la coordinación).
- VK-27: `Visible fields`: `Tracking Project`, `Linked Tracking`, `Type of Project`, `Agency`, `Permit Status`, `Revision Stage`, `Project Name`, `Submitted Date`, `Permit #`, `Permit Expires`.
- VK-28: `Details Panel`, en este orden (los títulos son sólo para ordenar; en Smartsheet se arrastran los campos):
  - Read-only: `Tracking Project`, `Linked Tracking`, `Type of Project`, `Agency`, `Customer`, `Project Name`, `Project Address`, `City`, `Design Ticket`, `Mile Post`, `Designers`, `Date Received`, `PM Approval Date`, `Revision Stage`.
  - Application: `LT`, `App Sent to Contractor`, `App Returned from Contractor`, `Submitted Date`, `Runner Submitting`.
  - 1st revision: `1st Revision Req`, `1st Revision Completed`, `Permit 1st Resubmitted`.
  - 2nd revision: `2nd Revision Req`, `2nd Revision Completed`, `Permit 2nd Resubmitted`.
  - Approval: `Runner Pick up`, `Permit #`, `Permit Approved`, `Permit Expires`, `Permit Fee`.
  - Status: `Permit Status`.
- VK-29: `Field Logic` (tres reglas; en cada una se eligen los campos a mostrar):
  - `Permit`: when `Type of Project` `is one of` `KMV-Permit`, `KMV-Line`, `KMV-Miscellaneous` → mostrar `LT`, `App Sent to Contractor`, `App Returned from Contractor`, `Submitted Date`, `Runner Submitting`, `Runner Pick up`, `Permit #`, `Permit Approved`, `Permit Expires`, `Permit Fee`, `Permit Status`.
  - `1st revision`: when `Revision Stage` `is one of` `1st Revision`, `2nd Revision` → mostrar `1st Revision Req`, `1st Revision Completed`, `Permit 1st Resubmitted`.
  - `2nd revision`: when `Revision Stage` `is one of` `2nd Revision` → mostrar `2nd Revision Req`, `2nd Revision Completed`, `Permit 2nd Resubmitted`.
  - `Revision Stage` la calcula la hoja (no se escribe): `1st Revision` cuando el permiso pasa a `4. Permit Needs Revision` o ya tiene `1st Revision Req`; `2nd Revision` cuando, ya reenviado (`Permit 1st Resubmitted`), vuelve a `4. Permit Needs Revision` o tiene `2nd Revision Req`; si no, `No revision`. Para que aparezca la primera revisión basta cambiar `Permit Status` a `4. Permit Needs Revision`.
- VK-30: `Sharing`: el equipo de permisos.

## 4. MOT y paquetes: `PROJECT KMV 2.0 - MOT & PACKAGES`

Origen: la hoja `MOT & Packages (Prototype)` (filas `Package` y `MOT`). Sólo lo que la persona de MOT usa de verdad (capturas del usuario, 2026-11-05, y historial 2026): nada más para no cargar la vista.

- VK-31: `General`: `Restrict view by current user`: sin restricción (corregido 2026-11-17 18:21: los paquetes los completa una sola persona para todos los proyectos, 15 de 17 en el historial, fuera quien fuera el `Permitting Team`; con la restricción vería sólo 1 de cada 5); sin filtro de hoja; `New Item Submission` = `Do Not Allow` (las filas `Package` salen al marcar `Prepare Packages` en el proyecto, o en un permiso que lleva su propio paquete; las `MOT`, de las hijas `KMV-MOT`).
- VK-32: `Visible fields`: `Tracking Project`, `Linked Tracking`, `Row Type`, `Project Name`, `MOT Status`, `Prepare Packages Request`, `Prepare Packages Completed`, `Design MOT Request`, `Design MOT Completed`.
- VK-33: `Details Panel`, en este orden:
  - Read-only: `Tracking Project`, `Linked Tracking`, `Row Type`, `Agency`, `Customer`, `Project Name`, `City`, `Designers`.
  - Packages: `Prepare Packages Request`, `Prepare Packages QC`, `Prepare Packages Completed`.
  - MOT design: `Design MOT Request`, `Design MOT QC`, `Design MOT Completed`, `Custom MOT`, `TYPICAL MOT`.
  - MOT permit (sólo lo que se usa seguido en 2026: `LT` en 134 de 152 MOT y `Submitted Date` en 128): `LT`, `Submitted Date`.
  - Status: `MOT Status`.
  - No van en la vista (siguen en la hoja, nada se pierde; se agregan si hicieran falta): `Permit #`, revisiones, `Permit Approved`, `Permit Expires` (usados en 14 o menos de 152).
- VK-34: `Field Logic` por `Row Type` (lista desde el 2026-11-17 16:27): regla `Package`: when `Row Type` `is one of` `Package` → mostrar `Prepare Packages Request`, `Prepare Packages QC`, `Prepare Packages Completed`; regla `MOT`: when `Row Type` `is one of` `MOT` → mostrar `Design MOT Request`, `Design MOT QC`, `Design MOT Completed`, `Custom MOT`, `TYPICAL MOT`, `LT`, `Submitted Date`.
- VK-35: `Sharing`: la persona de MOT y paquetes, con la cuenta con la que de verdad entra (el historial muestra una cuenta personal, no la de la empresa); el diseñador de MOT (llena `Design MOT QC` y pasa el estado a `5. Design MOT Needs QC`); y, si quiere, la coordinadora (en la 1.0 a veces llenaba `LT` y `Submitted Date` del MOT).
- VK-35b: automatizaciones de la hoja: ver `AUTOMATIZACIONES_KMV_2.0.md` AU-30 a AU-36 (las de todas las hojas están en esa guía).

## 5. Records: `PROJECT KMV 2.0 - RECORDS`

Origen: la hoja `Records Requests (Prototype)`.

- VK-36: `General`: `Restrict view by current user` = `Records Owner`; `New Item Submission` = `Do Not Allow` (las pide la coordinación con `Records Needed` o `Records Owner` en la fila del permiso, con `Agency`).
- VK-37: `Visible fields`: `Tracking Project`, `Linked Tracking`, `Project Name`, `Agency`, `Records Status`, `Record Request`, `Reminder Sent`, `Record Received`.
- VK-38: `Details Panel`: sólo lectura `Tracking Project`, `Customer`, `Agency`, `Project Name`, `Project Address`, `City`, `County`, `Date Received`; editables `Request Type`, `Send Method`, `Record Request`, `Reminder Sent`, `LT Records`, `PRR #`, `Future Project #`, `Security Key`, `Record Received`, `Records Status`, `Record Box`.
- VK-39: `Field Logic`: `PRR #` y `Security Key` sólo cuando `Request Type` es `PRR`; `Future Project #` sólo cuando es `Future Project`.
- VK-40: `Sharing`: el equipo de Records.

## 6. Facturación: `PROJECT KMV 2.0 - BILLING`

Origen: la hoja `Billing (Prototype)`.

- VK-41: `General`: sin restricción por usuario; `New Item Submission` = `Do Not Allow`.
- VK-42: `Visible fields`: `Tracking Project`, `Linked Tracking`, `Row Type`, `Customer`, `Project Name`, `Invoice Status`, `Purchase Orden`, `Invoice Sent`, `Invoice Paid`.
- VK-43: `Details Panel`: sólo lectura `Tracking Project`, `Type of Project`, `Customer`, `Project Name`, `Project Address`, `County`, `Agency`, `Contractor`, `Construction Manager`, `PM Approval Date`, `Project Status`, `Custom MOT`, `TYPICAL MOT`, `Additional Site Survey`, `Survey Certified`, `Tone Locating`, `Sonde FTG`, `GPR`, `Permit #`, `Permit Fee`, `Stamp And Signatures #`; editables el metraje (`Total Footage`, `UG`, `UG + Profile`, `ISP`, `Aerial`: facturación lo corrige aquí, pasa a la maestra y avisa por correo, SPEC-B19 FH-05c), `Purchase Orden`, `Invoice? GALP`, `Invoice? KMV`, `Customer invoice?`, `Invoice Completed (Galp)`, `PM Approval Invoice Date`, `Invoice Sent`, `Invoice Paid`; sólo lectura `Invoice Status`.
- VK-44: `Sharing`: sólo la persona de facturación.

## 7. Design Ticket y Mile Post: `PROJECT KMV 2.0 - DESIGN TICKETS`

Origen: la hoja `Design Tickets (Prototype)` (una fila por proyecto con `DT Owner`, la crea el servicio).

- VK-50: `General`: `Restrict view by current user` = `DT Owner`; `New Item Submission` = `Do Not Allow` (la fila sale al asignar `DT Owner` en el proyecto).
- VK-51: `Visible fields`: `Tracking Project`, `Linked Tracking`, `Project Name`, `Customer`, `City`, `Design Ticket`, `Mile Post`, `Project Status`, `Date Received`.
- VK-52: `Details Panel`: editables `Design Ticket` y `Mile Post` (primero); sólo lectura `Tracking Project`, `Project Name`, `Customer`, `Project Address`, `City`, `County`, `Date Received`, `Designers`, `Project Status`. Lo que se escribe vuelve a la maestra y de allí a `Permits`.
- VK-53: `Sharing`: las personas que son `DT Owner`.

## Formato condicional (colores de las hojas)

- VK-60 (2026-11-22, pedido del usuario): las hojas de trabajo tienen los mismos colores que la maestra `PROJECT KMV 2.0 (Prototype)`, cuyas 40 reglas no se tocaron. Las reglas se copiaron en el mismo orden (la de más arriba manda), con el estado de cada hoja en lugar de `Project Status` y sólo con los valores de su lista. Se dejaron fuera las que sólo nombran valores viejos que ya no están en la lista (`3. Permit Needs Revision`, `4. As-Built Revision`, `4. As-Built Required`, `KMV-AB`), las tapadas por otra más arriba (`1. Survey on Hold` naranja; `2. Design Revision Completed` y `4. Permit Revision Completed` rosa) y la de `Control Linked Tracking`, que sólo existe en la maestra.
- VK-61: `Permits` (20 reglas): colores de `Permit Status`; fila gris y tachada con `CANCELLED` o `4. No Permit Required`; fila azul `KMV-Miscellaneous`, lila `KMV-Permit` y `KMV-Line`.
- VK-62: `MOT & Packages` (10 reglas): colores de `MOT Status`; fila gris y tachada con `CANCELLED`, verde con `COMPLETE`; fila `MOT` rojo claro (como `KMV-MOT` en la maestra), fila `Package` azul (el paquete es del proyecto).
- VK-63: `Records Requests` (5 reglas nuevas y 1 que ya estaba): `Records Status` no existe en la maestra; se pintó con la misma paleta y el mismo sentido: `Received` verde, `No records` gris claro, `Not Received` rojo claro, `Ticket - coordination` naranja claro y `Not Appy` fila gris y tachada. La regla que ya estaba (fila lila si `Tracking Project` no está vacío) se movió al final para que no tape los estados.
- VK-64: `Billing` (34 reglas) y `Design Tickets` (31): `Type of Project` y `Project Status` (en `Design Tickets` sólo `Project Status`) pasaron de texto a lista desplegable con las opciones de la maestra; siguen bloqueadas, el servicio escribe igual y los valores no cambiaron (comprobado por API). Hacía falta porque en una regla Smartsheet sólo deja elegir valores de la lista o que ya estén en la hoja.
- VK-65: si se agrega o se renombra un estado en la maestra, sumarlo a la lista de `Billing` y `Design Tickets` y a las reglas de cada hoja donde aplique. Las reglas se ven y se cambian sólo en la interfaz (`Conditional Formatting`); la API no las lee.

## Cómo probar una vista

- VK-45: guardar (`Save`) y abrir la vista (`Back to view`). Agregar una fila: el panel debe pedir sólo lo de crear.
- VK-46: en `PROJECTS`, crear un proyecto y esperar su número (aparece `Pending ID` y en un minuto el número).
- VK-47: en `PERMITS`, crear un permiso con ese número en `Parent Project` y una `Agency`: en un minuto queda bajo el proyecto y aparece en `PERMITS TEAM`.
- VK-48: en `PERMITS TEAM`, cambiar `Permit Status`: en un minuto se ve como `Project Status` de esa fila en la coordinación.
