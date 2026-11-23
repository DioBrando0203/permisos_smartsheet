# Automatizaciones de la KMV 2.0: lista y para qué sirve cada una (AR-xx)

Estado 2026-11-22. Las 29 automatizaciones que existen hoy en las 6 hojas de la carpeta `PROJECT KMV 2.0 - Prototype` (Pruebas), leídas con `get_workflows`. Todas están apagadas: se encienden de a una para probarlas (`AUTOMATIZACIONES_KMV_2.0.md` AU-95). La guía con el detalle y el porqué de cada una es `AUTOMATIZACIONES_KMV_2.0.md` (AU-xx); aquí va el resumen para usar y decidir. Sin nombres de personas: se nombran por su rol.

## Cómo se agrupan

- AR-00: avisos de asignación (`DV | ...`): le llegan a quien recibe un trabajo, con el enlace a su vista. En las hojas de equipo la fila la crea el servicio cuando la coordinadora asigna en la maestra, así que el aviso sale en cuanto la coordinadora asigna (alrededor de un minuto).
- AR-01: alertas para el ingeniero (`Alert | ...` y `AUTO | QC ALERT`): el ingeniero es el jefe y se entera directamente de QC pendiente o demorado y de lo que está listo para facturar o sin cobrar (decisión del usuario, 2026-11-22).
- AR-02: automáticas sin correo (`Auto | ...`): ponen un valor o una fecha para que nadie tenga que acordarse.
- AR-03: ideas: creadas, apagadas y sin decidir; se quedan así hasta que el usuario diga (decisión del usuario, 2026-11-22).
- AR-04: en `MOT & Packages` los únicos avisos son los de asignación, cuando la coordinadora asigna un paquete o un MOT, y van sólo a la persona de MOT y paquetes (decisión del usuario, 2026-11-22).
- AR-05: los avisos llegan también a correos personales porque las automatizaciones están en `Unrestricted` (revisado por el usuario, AU-00j).

## Maestra `PROJECT KMV 2.0 (Prototype)` (10)

- AR-10 `DV | New Project` (AU-12): cuando cambia `Designers` en un proyecto `KMV-P` o `KMV-Miscellaneous` que ya tiene ID, avisa a los diseñadores con el enlace a `PROJECT KMV 2.0 - DESIGN`.
- AR-11 `DV | New Project (ID assigned)` (AU-13): el mismo aviso cuando el proyecto se creó con diseñador antes de tener ID; sale cuando llega el ID.
- AR-12 `AUTO | QC ALERT` (AU-15): cuando `Project Status` pasa a `2. Design Needs QC`, avisa al ingeniero.
- AR-13 `Alert | QC overdue` (AU-16): a las 9:00, si pasó más de 1 día desde `QC IN` y `QC OUT` sigue vacío, avisa al ingeniero con el enlace a la vista de diseño.
- AR-14 `Auto | QC IN date` (AU-15): con el mismo disparador que AR-12, pone la fecha en `QC IN` si está vacía; de ahí cuenta AR-13.
- AR-15 `Auto | Default Engineer` (AU-10): al crear un proyecto sin `Engineer`, pone al ingeniero por defecto.
- AR-16 `Auto | Default Surveyor` (AU-11): lo mismo con `Surveyor`.
- AR-17 `Client | Status Update` (AU-14): cuando `Project Status` cambia a uno de los 21 estados de cara al cliente y hay `Client Access`, le escribe al cliente con el estado y el enlace a `PROJECT KMV 2.0 - CUSTOMERS`. Sólo para producción (AU-00g).
- AR-18 `DV | New Records Request` y `DV | New Task Permitting Team` de la maestra (AU-04, AU-05): viejas, reemplazadas por AR-30 y AR-60; se borran cuando el usuario lo diga.

## `Permits (Prototype)` (4)

- AR-30 `DV | New Task Permitting Team` (AU-20): cuando se asigna o cambia `Permitting Team` en un permiso, avisa a esa persona con el enlace a `PROJECT KMV 2.0 - PERMITS TEAM`.
- AR-31 `Alert | Permit Needs Revision` (AU-21, idea): cuando `Permit Status` pasa a `4. Permit Needs Revision`, avisa a los diseñadores.
- AR-32 `Auto | Revision Request Date` (AU-22, idea): con el mismo disparador, pone la fecha en `1st Revision Req` o, si ya hubo reenvío, en `2nd Revision Req`; así la vista muestra sola la revisión que toca.
- AR-33 `Alert | Permit Expiring` (AU-23, idea): 30 días antes de `Permit Expires`, si el permiso no está cerrado, avisa a `Permitting Team` y a la coordinadora.

## `MOT & Packages (Prototype)` (7)

- AR-40 `DV | New Package` (AU-32): cuando la coordinadora pide un paquete (llega la fila `Package`), avisa a la persona de MOT y paquetes con el enlace a `PROJECT KMV 2.0 - MOT & PACKAGES`.
- AR-41 `DV | New MOT` (AU-33): lo mismo cuando llega una fila `MOT`.
- AR-42 `Auto | Package Request Date` (AU-30): pone la fecha en `Prepare Packages Request` al llegar la fila `Package` (en la 1.0 la ponía la coordinadora a mano).
- AR-43 `Auto | MOT Request Date` (AU-31): pone la fecha en `Design MOT Request` al llegar la fila `MOT`.
- AR-44 `Alert | MOT Needs QC` (AU-34, idea): aviso cuando `MOT Status` pasa a `5. Design MOT Needs QC`.
- AR-45 `Auto | Packages Completed` (AU-35, idea): al llenar `Prepare Packages Completed`, pone `MOT Status` en `3. Packages Completed`.
- AR-46 `Alert | MOT Design Completed` (AU-36, idea): aviso cuando `MOT Status` pasa a `5. Design MOT Completed`.

## `Records Requests (Prototype)` (5)

- AR-60 `DV | New Records Request` (AU-40): cuando se asigna o cambia `Records Owner`, avisa a esa persona con el enlace a `PROJECT KMV 2.0 - RECORDS`.
- AR-61 `Auto | LT Records on status` (AU-41): cada vez que cambia `Records Status`, pone la fecha en `LT Records` (viene de la 1.0).
- AR-62 `Auto | LT Records on PRR #` y `Auto | LT Records on Future Project #` (AU-42): al llenar el número, ponen la fecha en `LT Records` (viene de la 1.0).
- AR-63 `Alert | Records Reminder` (AU-43, idea): 7 días después de `Record Request`, si no llegó nada, avisa a `Records Owner` para recordarle a la agencia.

## `Billing (Prototype)` (2)

- AR-70 `Alert | Ready to send invoice` (AU-50): cuando se llena `PM Approval Invoice Date` y la factura no se envió, avisa al ingeniero con el enlace a `PROJECT KMV 2.0 - BILLING`.
- AR-71 `Alert | Sent without payment (weekly)` (AU-51): los lunes a las 9:00, manda al ingeniero la lista de facturas enviadas al cliente y todavía sin pagar.

## `Design Tickets (Prototype)` (1)

- AR-80 `DV | New Design Ticket` (AU-60): cuando se asigna o cambia `DT Owner`, avisa a esa persona con el enlace a `PROJECT KMV 2.0 - DESIGN TICKETS`.

## Para encender

- AR-90: primero los avisos de asignación (AR-10, AR-11, AR-30, AR-40, AR-41, AR-60, AR-80) y las alertas del ingeniero (AR-12, AR-13, AR-70, AR-71), con las automáticas que las acompañan (AR-14, AR-15, AR-16, AR-42, AR-43, AR-61, AR-62), de a una y con el backend encendido.
- AR-91: las ideas (AR-31 a AR-33, AR-44 a AR-46, AR-63) sólo si el usuario las aprueba; AR-17 al pasar a producción.
- AR-92: los avisos de asignación dependen de que cada persona tenga correo en `Contact List` (K2-89).
