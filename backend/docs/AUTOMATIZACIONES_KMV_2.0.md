# Automatizaciones de la KMV 2.0 (AU-xx)

Estado 2026-11-18 15:50. Qué automatizaciones necesita cada hoja de la 2.0 ahora que el trabajo está repartido en hojas de equipo. Sale de las automatizaciones de la 1.0 (hoja `PROJECT KMV 1.0.0` y hojas `Engineering Plan` 2026, leídas por API), de las 6 que ya armó el usuario en la maestra 2.0 y del historial 2026. Las crea el usuario en cada hoja: `Automation` > `Create workflow from scratch`. Nombres y textos en inglés. Vistas: `VISTAS_KMV_2.0.md`; estado general: `KMV_2.0.md`.

Prioridad de cada una: obligatoria (sin ella se pierde algo que hoy existe), recomendada (ayuda clara) u opcional.

## Reglas generales

- AU-00a: un flujo tiene un solo disparador (`Trigger`); dentro puede tener condiciones y varias acciones en orden (por ejemplo, registrar una fecha y avisar).
- AU-00b: lo que escribe el servicio (filas nuevas en las hojas de equipo, datos copiados, estados que vuelven a la maestra, el ID) también dispara automatizaciones, igual que si lo escribiera una persona.
- AU-00c: cada aviso sale de la hoja donde trabaja quien lo recibe y lleva el enlace a su vista. Por eso los avisos de permisos, Records y Design Ticket pasan de la maestra a su hoja: allí la fila sólo existe cuando ya tiene su ID (nunca llega un `Pending ID`) y la persona la encuentra en su vista. Un mismo aviso no debe quedar en las dos hojas: llegarían dos correos.
- AU-00d: `Alert someone` > `Contacts in a cell` usa el correo guardado en la celda. Quién aparece en `Designers`, `Permitting Team`, `Records Owner` y `DT Owner` se maneja en `Contact List` (`KMV_2.0.md` K2-89): una persona sin correo no recibe avisos.
- AU-00e: el enlace de cada vista se copia desde la vista ya armada (el de la 1.0 apunta a las vistas viejas).
- AU-00f: no usar como disparador una columna con `TODAY()` (`QC # Days`, `Process # Days` y las demás de días): cambia sola cada día. Se usa el estado o la fecha de origen.
- AU-00g: `Client | Status Update` escribe a los contactos reales de cada cliente (`Client Access` sale de `Customer List`). En el prototipo se deja apagada, o se prueba con un cliente cuyos contactos sean internos.
- AU-00h: en los textos se insertan campos con `{{`: por ejemplo `{{Tracking Project}}`.

## Lo que ya está armado en la maestra (revisión de la captura)

- AU-01: `Auto | Default Engineer` y `Auto | Default Surveyor.`: se quedan en la maestra (AU-10, AU-11). Quitar el punto final del segundo nombre.
- AU-02: `AUTO | QC ALERT`: hoy se dispara cuando cambia `QC # Days`, que es fórmula con `TODAY()` (AU-00f). Rehacer como AU-15.
- AU-03: `DV | New Project`: hoy avisa a una persona fija. Debe avisar a `Contacts in a cell` `Designers`, como en la 1.0 (AU-12 y AU-13).
- AU-04: `DV | New Records Request`: hoy se dispara con cualquier cambio de la fila. Pasa a la hoja de Records (AU-40); en la maestra se borra.
- AU-05: `DV | New Task Permitting Team`: pasa a la hoja `Permits` (AU-20); en la maestra se borra.
- AU-06: falta `Client | Status Update` (AU-14).

## Maestra `PROJECT KMV 2.0 (Prototype)`

- AU-10 `Auto | Default Engineer` (obligatoria; ya creada).
  - Trigger: `When rows are added`.
  - Conditions: `Engineer` `is blank`; `Type of Project` `is one of` `KMV-P`, `KMV-Miscellaneous`.
  - Action: `Change cell value`: `Engineer` = la persona por defecto.
- AU-11 `Auto | Default Surveyor` (obligatoria; ya creada): igual que AU-10 con `Surveyor`.
- AU-12 `DV | New Project` (obligatoria; viene de la 1.0).
  - Trigger: `When rows are added or changed` > `Designers` changes (to any value).
  - Conditions: `Designers` `is not blank`; `Stable Tracking Project` `is not blank`; `Type of Project` `is one of` `KMV-P`, `KMV-Miscellaneous`.
  - Action: `Alert someone` > `Contacts in a cell`: `Designers`.
  - Subject: `New Task: {{Tracking Project}} – {{Project Name}}`.
  - Message: `You have a new task: "NEW PROJECT"`, más el enlace de la vista `DESIGN`.
  - Fields: `Tracking Project`, `Linked Tracking`, `Project Name`, `Project Address`, `City`, `County`, `Design Ticket`, `Project Status`.
- AU-13 `DV | New Project (ID assigned)` (obligatoria; nueva). Cubre el proyecto creado con diseñador antes de tener ID: AU-12 lo salta por su condición y este avisa cuando llega el ID.
  - Trigger: `When rows are added or changed` > `Stable Tracking Project` changes.
  - Conditions: `Designers` `is not blank`; `Type of Project` `is one of` `KMV-P`, `KMV-Miscellaneous`.
  - Action, subject, message y fields: los de AU-12.
- AU-14 `Client | Status Update` (obligatoria en producción; viene de la 1.0; apagada en el prototipo, AU-00g).
  - Trigger: `When rows are changed` > `Project Status` changes to uno de los 21 estados que ya usaba la 1.0 (los de cara al cliente: trámite, permiso, MOT aprobado, cierre y cancelación; no los internos de diseño).
  - Conditions: `Client Access` `is not blank`.
  - Action: `Alert someone` > `Contacts in a cell`: `Client Access`.
  - Subject: `Project Update – {{Tracking Project}}: {{Project Status}}`.
  - Message: el de la 1.0 (saludo; `Project`, `Tracking #` y `Current status`; enlace de la vista de clientes de la 2.0, que falta armar: `KMV_2.0.md` K2-87b).
  - En la 2.0 el estado de cada permiso vuelve solo desde `Permits` y `MOT & Packages` (AU-00b), así que el cliente recibe lo mismo que en la 1.0.
- AU-15 `AUTO | QC ALERT` (recomendada; rehecha).
  - Trigger: `When rows are added or changed` > `Project Status` changes to `2. Design Needs QC`.
  - Action: `Alert someone` > a la persona de QC (personas fijas).
  - Va en dos flujos con el mismo disparador: éste avisa y `Auto | QC IN date` registra la fecha en `QC IN` si está vacía (Smartsheet no aceptó las dos acciones en un solo flujo).
  - Fields: `Tracking Project`, `Project Name`, `Designers`, `QC IN`.
- AU-16 `Alert | QC overdue` (opcional; nueva; es lo que buscaba `QC # Days`).
  - Trigger: `When a date is reached`: 2 días después de `QC IN`.
  - Conditions: `QC OUT` `is blank`.
  - Action: `Alert someone` > la persona de QC y la coordinación. Hora: 9:00.

## `Permits (Prototype)`

- AU-20 `DV | New Task Permitting Team` (obligatoria; viene de la maestra de la 1.0).
  - Trigger: `When rows are added or changed` > `Permitting Team` changes. Sirve para la fila nueva y para una reasignación (el servicio copia el cambio desde la maestra).
  - Conditions: `Permitting Team` `is not blank`.
  - Action: `Alert someone` > `Contacts in a cell`: `Permitting Team`.
  - Subject: `New Task: {{Tracking Project}} – {{Project Name}} – {{Agency}}`.
  - Message: `You have a new task: "PERMIT"`, más el enlace de la vista `PERMITS TEAM`.
  - Fields: `Tracking Project`, `Linked Tracking`, `Type of Project`, `Agency`, `Project Name`, `Project Address`, `City`, `County`, `Permit Status`, `LT`.
- AU-21 `Alert | Permit Needs Revision` (recomendada; nueva). La revisión la hace diseño, así que se le avisa al instante.
  - Trigger: `When rows are added or changed` > `Permit Status` changes to `4. Permit Needs Revision`.
  - Action: `Alert someone` > `Contacts in a cell`: `Designers`.
  - Subject: `Revision requested: {{Tracking Project}} – {{Agency}}`.
  - Fields: `Tracking Project`, `Agency`, `Project Name`, `Revision Stage`, `Permitting Team`.
- AU-22 `Auto | Revision Request Date` (opcional; nueva). Un flujo con dos caminos de condición:
  - Trigger: el de AU-21 (puede ser el mismo flujo, con estas acciones antes del aviso).
  - Camino 1: `1st Revision Req` `is blank` → `Record a date` en `1st Revision Req`.
  - Camino 2: `Permit 1st Resubmitted` `is not blank` y `2nd Revision Req` `is blank` → `Record a date` en `2nd Revision Req`.
  - Así `Revision Stage` cambia solo y la vista muestra la revisión que toca.
- AU-23 `Alert | Permit Expiring` (recomendada; nueva).
  - Trigger: `When a date is reached`: 30 días antes de `Permit Expires`.
  - Conditions: `Permit Status` `is not one of` `4. Permit Closed`, `4. Permit Cancelled`, `8. Close - Permit Process`, `CANCELLED`.
  - Action: `Alert someone` > `Contacts in a cell`: `Permitting Team` (y la coordinación).
  - Fields: `Tracking Project`, `Agency`, `Permit #`, `Permit Expires`, `Project Name`.

## `MOT & Packages (Prototype)`

Reemplaza a VISTAS VK-35b. La persona de MOT y paquetes no sale de una columna de asignación (la vista va sin restricción por usuario), así que sus avisos van a personas fijas, con la cuenta con la que entra (`KMV_2.0.md` K2-85e).

- AU-30 `Auto | Package Request Date` (obligatoria). En la 1.0 la fecha la ponía la coordinadora al marcar la casilla; en la 2.0 esa columna no está en su vista.
  - Trigger: `When rows are added`.
  - Conditions: `Row Type` `is one of` `Package`.
  - Action: `Record a date` en `Prepare Packages Request`.
- AU-31 `Auto | MOT Request Date` (obligatoria). En la 1.0 también la ponía la coordinadora (9 de 9 en el historial).
  - Trigger: `When rows are added`.
  - Conditions: `Row Type` `is one of` `MOT`.
  - Action: `Record a date` en `Design MOT Request`.
- AU-32 `DV | New Package` (recomendada; puede ir como segunda acción de AU-30).
  - Action: `Alert someone` > la persona de MOT y paquetes.
  - Subject: `New Task: {{Tracking Project}} – {{Project Name}} – PACKAGE`.
  - Message: `You have a new task: "PACKAGE"`, más el enlace de la vista `MOT & PACKAGES`.
  - Fields: `Tracking Project`, `Linked Tracking`, `Row Type`, `Agency`, `Project Name`, `City`, `Permitting Team`.
- AU-33 `DV | New MOT` (recomendada; puede ir como segunda acción de AU-31).
  - Action: `Alert someone` > la persona de MOT y paquetes y el diseñador de MOT.
  - Subject: `New Task: {{Tracking Project}} – {{Project Name}} – MOT`.
  - Fields: los de AU-32.
- AU-34 `Alert | MOT Needs QC` (recomendada; nueva). En la 1.0 el diseñador de MOT pasa a `5. Design MOT Needs QC` y la persona de MOT completa.
  - Trigger: `When rows are added or changed` > `MOT Status` changes to `5. Design MOT Needs QC`.
  - Action: `Alert someone` > la persona de MOT y paquetes.
- AU-35 `Auto | Packages Completed` (opcional). En la 1.0 ese estado lo ponía a mano la persona de MOT; esto sólo le ahorra un paso.
  - Trigger: `When rows are added or changed` > `Prepare Packages Completed` changes.
  - Conditions: `Prepare Packages Completed` `is not blank`.
  - Action: `Change cell value`: `MOT Status` = `3. Packages Completed`.
- AU-36 `Alert | MOT Design Completed` (opcional; nueva).
  - Trigger: `MOT Status` changes to `5. Design MOT Completed`.
  - Action: `Alert someone` > la coordinación, para seguir con el permiso de MOT.

## `Records Requests (Prototype)`

- AU-40 `DV | New Records Request` (obligatoria; viene de la maestra de la 1.0).
  - Trigger: `When rows are added or changed` > `Records Owner` changes.
  - Conditions: `Records Owner` `is not blank`.
  - Action: `Alert someone` > `Contacts in a cell`: `Records Owner`.
  - Subject: `New Task: {{Tracking Project}} – {{Project Name}} – {{Agency}}`.
  - Message: `You have a new task: "RECORDS REQUEST"`, más el enlace de la vista `RECORDS`.
  - Fields: `Tracking Project`, `Linked Tracking`, `Agency`, `Project Name`, `Project Address`, `City`, `County`, `Date Received`, `Request Type`.
- AU-41 `Auto | LT Records on status` (obligatoria; viene de la 1.0, "LT Records al cambiar Records Status").
  - Trigger: `When rows are added or changed` > `Records Status` changes.
  - Action: `Record a date` en `LT Records`.
- AU-42 `Auto | LT Records on number` (recomendada; viene de la 1.0, "LT Records al llenar Record ID"; hoy `Record ID` son `PRR #` y `Future Project #`).
  - Trigger: `When rows are added or changed` > `PRR #` changes (otro flujo igual para `Future Project #`).
  - Conditions: la columna `is not blank`.
  - Action: `Record a date` en `LT Records`.
- AU-43 `Alert | Records Reminder` (opcional; nueva).
  - Trigger: `When a date is reached`: 7 días después de `Record Request`.
  - Conditions: `Record Received` `is blank`; `Records Status` `is not one of` `Received`, `No records`.
  - Action: `Alert someone` > `Contacts in a cell`: `Records Owner` (mandar recordatorio a la agencia).

## `Billing (Prototype)`

Vienen de `Invoices (Piloto)` de la 1.0, que las tenía apagadas. `Invoice Status` (fórmula) vale `NOT INVOICED`, `GALP INVOICED`, `PM APPROVED`, `SENT TO CUSTOMER` o `PAID`.

- AU-50 `Alert | Ready to send invoice` (recomendada).
  - Trigger: `When rows are added or changed` > `PM Approval Invoice Date` changes.
  - Conditions: `PM Approval Invoice Date` `is not blank`; `Invoice Sent` `is blank`.
  - Action: `Alert someone` > la persona de facturación.
  - Fields: `Tracking Project`, `Customer`, `Project Name`, `Purchase Orden`, `Permit #`, `Total Footage`.
- AU-51 `Alert | Sent without payment (weekly)` (recomendada).
  - Trigger: `When a date is reached` con repetición semanal (por ejemplo, los lunes).
  - Conditions: `Invoice Status` `is one of` `SENT TO CUSTOMER`.
  - Action: `Alert someone` > la persona de facturación (una lista con todas las filas pendientes).
  - Fields: `Tracking Project`, `Customer`, `Invoice Sent`, `Invoice # Days`.

## `Design Tickets (Prototype)` (sólo si la hoja se queda, `KMV_2.0.md` K2-87)

- AU-60 `DV | New Design Ticket` (obligatoria si la hoja se queda).
  - Trigger: `When rows are added or changed` > `DT Owner` changes.
  - Conditions: `DT Owner` `is not blank`.
  - Action: `Alert someone` > `Contacts in a cell`: `DT Owner`.
  - Subject: `New Task: {{Tracking Project}} – {{Project Name}} – DESIGN TICKET`.
  - Message: `You have a new task: "DESIGN TICKET"`, más el enlace de la vista `DESIGN TICKETS`.
  - Fields: `Tracking Project`, `Linked Tracking`, `Customer`, `Project Name`, `Project Address`, `City`, `County`, `Date Received`, `Designers`.

## Avance

- AU-80 (2026-11-18 16:06, comprobado con el conector de Smartsheet, `get_workflows`): la maestra tiene 10 flujos, todos apagados para probarlos de a uno: AU-10, AU-11, AU-12, AU-13, AU-14, AU-15 (`AUTO | QC ALERT` y `Auto | QC IN date`), AU-16 y las viejas AU-04 y AU-05.
- AU-81: falta en la maestra: los enlaces de las vistas de la 2.0 (`DESIGN` en AU-12 y AU-13; clientes en AU-14, vista que aún no existe); a quién va QC (AU-15 y AU-16 avisan hoy a una sola persona fija) y si se suma la coordinación a AU-16; correos de los diseñadores en `Contact List` (K2-89).
- AU-82: siguiente: hojas de equipo, de a una (`Permits`, `MOT & Packages`, Records, `Billing`; `Design Tickets` si se queda). Recién cuando existan AU-20 y AU-40 se borran de la maestra AU-04 y AU-05 (borrar no tiene vuelta atrás).

## Orden sugerido

- AU-90: obligatorias primero: AU-12, AU-13, AU-20, AU-30, AU-31, AU-40, AU-41 (y AU-60 si `Design Tickets` se queda); ajustar AU-10 y AU-11; borrar de la maestra las viejas de Records y permisos (AU-04, AU-05).
- AU-91: después las recomendadas: AU-15, AU-21, AU-23, AU-32, AU-33, AU-34, AU-42, AU-50, AU-51.
- AU-92: AU-14 (`Client | Status Update`) al pasar a producción, o antes con un cliente de prueba.
- AU-93: las opcionales según haga falta: AU-16, AU-22, AU-35, AU-36, AU-43.

## Cómo probar

- AU-95: activar una a la vez y probar con filas de prueba del prototipo, con el backend encendido. Por ejemplo, un proyecto nuevo con diseñador y `Permitting Team`, y un permiso con `Agency`. En un minuto debe llegar `DV | New Project` con el ID (AU-13); en menos de un minuto más, `DV | New Task Permitting Team` desde `Permits` (AU-20).
- AU-96: una reasignación: cambiar `Permitting Team` del proyecto en la maestra; el servicio lo copia a `Permits` y llega un aviso por cada permiso del proyecto (los que no tienen otra persona propia), sólo a la persona nueva y ninguno desde la maestra.
- AU-97: mientras `Contact List` no esté completa (K2-89), sólo reciben avisos las personas que ya tienen correo en las columnas.
