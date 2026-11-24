# Vistas sobre 8. Others - Engineering Plan 2026 (VA-10 a VA-19)

Hoja de producción `8. Others - Engineering Plan 2026` (`8569789430583172`, workspace `Workspace`, fuera de Pruebas: sólo lectura para nosotros). Las tres vistas y sus avisos los creó la cuenta dueña el 2026-11-10 (avisos retocados el 2026-11-11). Según el usuario funcionaban bien: fue la prueba sobre una hoja real con el modelo de la 1.0 (una vista por equipo, restringida por la columna de correo, y un aviso con el enlace). Estado: borradas el 2026-11-23 a pedido del usuario. Verificado antes de borrar (sólo lectura): tabla, panel, restricción y accesos iguales a lo documentado abajo; los tres avisos de la hoja siguen encendidos y quedarán con el enlace roto (VA-15).

## VA-10 `8. Others - Engineering Plan 2026 DESIGNERS`

- Id `5d04c0c0-6342-4816-b038-17aa6a65e485`; último uso de la cuenta dueña 2026-11-10.
- Restricción por usuario: `Email Designer1`. Sin filtro de hoja ni filtros de vista.
- Tabla (13): `Tracking Project`, `Linked Tracking`, `Project Name`, `Project Address`, `City`, `County`, `QC IN`, `QC OUT`, `QC # Days`, `Record Box`, `LT Records`, `Project Status`, `Design Ticket`.
- Panel (2): `Project Status`, `QC IN`.
- Comentarios visibles sin poder agregar; adjuntos visibles sin poder agregar; sin exportar.
- Compartida con `DV Designers` y 1 persona.
- Aviso `DV | Aviso asignacion Designer1` (activo): `Alert someone` a `Email Designer1`, inmediato, asunto `New Project Others`, mensaje `New Task for Designers:` con el enlace a la vista, 7 columnas en el correo.

## VA-11 `8. Others - Engineering Plan 2026 PERMITTING TEAM`

- Id `19bef5b1-3049-410b-9a05-540875ee43c5`; último uso 2026-11-10.
- Restricción por usuario: `Email Permitting Team`. Sin filtros.
- Tabla (49, casi toda la hoja): `Type of Project`, `Tracking Project`, `Linked Tracking`, `Task`, `Project Name`, `Project Address`, `City`, `County`, `Permit #`, `LT`, `Agency`, `Project Status`, `Obs`, `Priority`, `Construction Manager`, `Customer`, `Submitted Date`, `Permit Approved`, `Permit Expires`, `Record Request`, `PM Approval Date`, `Record Received`, `Record # Days`, `Record Box`, `Prepare Packages`, `Prepare Packages Request`, `Prepare Packages QC`, `Prepare Packages Completed`, `Prepare Packages # Days`, `Permit Coordinator Approved Date (QC)`, `App Sent to Contractor`, `App Returned from Contractor`, `App Delay Days from Contractor`, `Runner Submitting`, `Runner Pick up`, `Process # Days`, `Permit # Days`, `1st Revision Req`, `2nd Revision Req`, `2nd Revision Completed`, `Design - Days in 2nd Revision`, `Permit - Days in 2nd Revision`, `Permit - Days in 1st Revision`, `Permit 1st Resubmitted`, `1st Revision Completed`, `Permit - Days in Submitted`, `Design - Days in 1st Revision`, `Permit 2nd Resubmitted`, `Permit Fee`.
- Panel (12): `LT`, `Permit #`, `Permit Fee`, `Project Status`, `PM Approval Date`, `Submitted Date`, `App Sent to Contractor`, `App Returned from Contractor`, `Runner Submitting`, `Runner Pick up`, `Permit Approved`, `Obs`.
- Comentarios y adjuntos visibles y se pueden agregar; sin exportar.
- Compartida con `DV Permit Team` y 2 personas.
- Aviso `DV | Aviso asignacion Permitting Team` (activo): a `Email Permitting Team`, asunto `New Project Others`, mensaje `Permits:` con el enlace.

## VA-12 `8. Others - Engineering Plan 2026 RECORDS`

- Id `3cda547d-88a5-44d7-8689-abe5fdf4691a`; último uso 2026-11-10.
- Restricción por usuario: `Email Designer2` (en esta hoja `Designer2` era la persona de Records).
- Tabla (16): `Tracking Project`, `Linked Tracking`, `Project Name`, `Project Address`, `City`, `County`, `Date Received`, `Agency`, `Record Request`, `Record ID`, `LT Records`, `Record Received`, `Records Status`, `Record Box`, `Design Ticket`, `Record # Days`.
- Panel (7): `Record Request`, `Record ID`, `LT Records`, `Record Received`, `Records Status`, `Record Box`, `Design Ticket`.
- Comentarios y adjuntos visibles y se pueden agregar; sin exportar.
- Compartida con `DV Permit Team` y 2 personas.
- Aviso `DV | Aviso asignacion Designer2` (activo): a `Email Designer2`, asunto `New Project Others`, mensaje `Records Request:` con el enlace.

## Qué funcionó y qué pasó a la 2.0

- VA-13: el circuito completo funcionaba: la coordinadora asigna, el aviso llega con el enlace y la persona ve sólo sus filas. En la 2.0 se mantiene, con una sola columna de contacto por equipo y el aviso saliendo de la hoja del equipo (`../AUTOMATIZACIONES_KMV_2.0.md` AU-00c, AU-00j).
- VA-14: la tabla de permisos con 49 columnas era la hoja entera: la 2.0 usa tablas cortas y paneles por tipo (`../KMV_2.0.md` K2-94, `../VISTAS_KMV_2.0.md` VK-27 a VK-29).
- VA-15: si se borran estas vistas, los tres avisos activos de la hoja de producción siguen enviando el enlace roto; apagarlos o cambiarlos es una escritura en producción que sólo puede hacer el usuario. Resuelto el 2026-11-23: el usuario apagó los tres avisos; comprobado por API (sólo lectura), la hoja quedó con 0 avisos encendidos de 5.
