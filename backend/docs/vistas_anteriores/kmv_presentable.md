# Vistas sobre PROJECT KMV, maestra anterior a la 1.0.0 (VA-40 a VA-49)

Hoja `PROJECT KMV` (`5254686035890052`, Pruebas): la maestra con la que se armó el modelo de la 1.0 (después copiada como `PROJECT KMV 1.0.0`, ver `kmv_1_0_0.md` y `../HOJA_PROJECT_KMV.md` HK-04). Vistas creadas del 2026-11-10 al 2026-11-12; sus avisos están en esta hoja y en la 1.0.0. Filtros compartidos de la hoja: `Open` (`Closed` sin marcar, PEN-27) y `Filter By Costumer`.

## VA-41 `KMV - Designers`

- Id `482e8b5d-cf2f-4330-9d41-faba46552fdb`; último uso de la cuenta dueña 2026-11-12. Estado: se queda (la enlazan avisos de la 2.0, README VA-09).
- Restricción por usuario: `Email Designer1`. Sin filtro de hoja.
- Tabla (21): `Task`, `Tracking Project`, `Linked Tracking`, `Project Name`, `Project Address`, `City`, `County`, `Drawing Due Date`, `Project # Days`, `QC IN`, `QC OUT`, `QC # Days`, `Record Box`, `LT Records`, `Design Ticket`, `Project Status`, `Total Footage`, `UG`, `UG + Profile`, `ISP`, `Aerial`.
- Panel (7): `Project Status` visible; `QC IN`, `Total Footage`, `UG`, `UG + Profile`, `ISP` y `Aerial` ocultos.
- Comentarios visibles sin poder agregar; adjuntos visibles sin poder agregar; sin exportar.
- Compartida con `DV Designers` y 1 persona.

## VA-42 `KMV - PERMITS`

- Id `fef91195-cab5-4495-8987-359d946483cc`; último uso 2026-11-12. Estado: se borra.
- Restricción por usuario: `Email Permitting`. Filtro de hoja `Open`: la fila cerrada desaparecía de la vista (comprobado por el usuario el 2026-11-11, PEN-27).
- Tabla (15): `Tracking Project`, `Linked Tracking`, `Project Name`, `Project Address`, `City`, `County`, `Permit #`, `LT`, `Project Status`, `Construction Manager`, `Customer Code`, `Submitted Date`, `Permit Approved`, `Permit Expires`, `PM Approval Date`.
- Panel (5): `Permit #`, `LT`, `Submitted Date`, `App Sent to Contractor`, `Project Status`.
- Comentarios y adjuntos visibles y se pueden agregar; exportar a .csv permitido.
- Compartida con `DV Permit Team`.

## VA-43 `KMV - RECORDS DV`

- Id `b21c185f-b7d4-4b25-91b7-f117a9238de5`; último uso 2026-11-13. Estado: se borra.
- Restricción por usuario: `Email Designer2`. Permitía agregar filas (`New Item Submission`, a `PROJECT KMV`).
- Tabla (16): `Tracking Project`, `Agency`, `Project Name`, `Project Address`, `City`, `County`, `Send Method`, `Record Request`, `LT Records`, `Future Project #`, `PRR #`, `Security Key`, `Record Received`, `Records Status`, `Record Box`, `Record # Days`.
- Panel (10): `Send Method`, `Record Request`, `Request Type`, `PRR #`, `Security Key`, `Future Project #`, `LT Records`, `Record Received`, `Records Status`, `Record Box`.
- Comentarios y adjuntos visibles y se pueden agregar; exportar permitido.
- Compartida con `DV Permit Team` y 1 persona.

## VA-44 `KMV - MP/DT DV`

- Id `eb2d1293-2c62-450f-9ab5-03cee9cf3a66`; último uso 2026-11-11. Estado: se borra.
- Restricción por usuario: `DT Owner`. Permitía agregar filas (a `PROJECT KMV`).
- Tabla (8): `Tracking Project`, `Linked Tracking`, `Project Name`, `Project Address`, `City`, `County`, `Design Ticket`, `Mile Post`.
- Panel (2): `Design Ticket`, `Mile Post`.
- Comentarios y adjuntos visibles y se pueden agregar; sin exportar.
- Compartida con `DV Permit Team` y 1 persona.

## VA-45 `KMV - CUSTOMERS`

- Id `70132910-6338-4f25-a814-d15aff143bbe`; último uso 2026-11-12. Estado: se queda hasta armar la vista de clientes de la 2.0 (README VA-09).
- Restricción por usuario: `Client Access` (cada cliente ve sus filas, también las cerradas: sin filtro `Open`, `../HOJA_PROJECT_KMV.md` HK-32).
- Tabla (10): `Tracking Project`, `Project Name`, `Date Received`, `Submitted Date`, `Permit Approved`, `Permit Expires`, `Project Status`, `Agency`, `Permit #`, `Obs`.
- Sin panel de edición (sólo lectura); comentarios visibles sin poder agregar; sin adjuntos; exportar permitido.
- Compartida con `DV Permit Team`.

## Avisos de PROJECT KMV que enlazan a estas vistas

- VA-46: `DV | New Task Designer1` (activo): a `Email Designer1`, asunto `New Task: <Tracking Project> – <Project Name>`, mensaje `New Task: "NEW PROJECT"` con proyecto, nombre y enlace a VA-41.
- VA-47: `DV | New Task Permitting Team` (activo): a `Email Permitting`, asunto `New Task`, mensaje `You have a new Task: "PERMITS"` con enlace a VA-42.
- VA-48: `DV | New Task Designer2` (activo): a `Email Designer2`, asunto con proyecto, nombre y agencia, mensaje `You have a new task: "RECORDS REQUEST"` con enlace a VA-43; y `Client | Status Update` (activo): a `Client Access`, aviso al cliente con proyecto, número y estado, y enlace a VA-45.
- VA-49: al borrar VA-42 y VA-43, `DV | New Task Permitting Team` y `DV | New Task Designer2` de esta hoja quedan con el enlace roto. Es una hoja de Pruebas que el servicio ya no procesa; si se vuelve a usar, apagar o cambiar esos avisos.
