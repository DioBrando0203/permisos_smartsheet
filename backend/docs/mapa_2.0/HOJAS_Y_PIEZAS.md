# Hojas, vistas, reportes y automatizaciones de la 2.0 (MP-10 a MP-59)

Estado 2026-11-23, comprobado con lecturas por API y en la aplicación de Dynamic View. Los nombres llevan "(Prototype)" mientras la 2.0 esté en prueba. Sin nombres de personas: se nombran por su rol.

## Hoja principal (maestra)

- MP-10: `PROJECT KMV 2.0 (Prototype)` (`1979884168761220`), 79 columnas; capacidad para unas 6 329 filas por año (2026 proyecta unas 4 230).
- MP-11: qué guarda: el proyecto (cliente, nombre, dirección, fechas), el diseño (QC, metraje, as-built), las asignaciones (`Designers`, `Permitting Team`, `Records Owner`, `DT Owner`) y los resúmenes que vuelven de las hojas de equipo.
- MP-12: filas madre: proyectos `KMV-P` (diseño) y `KMV-Miscellaneous` (permisos). Filas hija: trámites `KMV-Permit`, `KMV-Line` y `KMV-MOT`, siempre debajo de su proyecto.
- MP-13: quién escribe: la coordinadora crea proyectos y trámites (desde vistas); diseño llena lo suyo desde su vista; el servicio pone el ID, mueve los trámites bajo su proyecto y escribe los resúmenes (bloqueados).
- MP-14: lo que calcula sola con fórmulas: `Tracking Project` (el ID visible), los días (`... # Days`), `Phase` y `Closed` (desde `Project Status List`), `Client Access` (desde `Customer List`) y `Records Status` (desde la hoja de Records: `Complete` cuando todos los pedidos del proyecto tienen `Record Box`, si no `Received`, `No records` o `Pending (n/m received)`).

## Hojas de equipo (hijas)

Todas llevan los datos del proyecto copiados y bloqueados, `Linked Tracking` y una columna oculta `Master Row` que las une con su fila de la maestra. Las filas las crea el servicio; nadie las crea a mano.

- MP-20: `Permits (Prototype)` (`3435959686483844`, 44 columnas): una fila por permiso o línea, y por proyecto `KMV-Miscellaneous`. El equipo de permisos lleva el trámite (`Permit Status`, fechas, revisiones, `Permit #`). Vuelven a la maestra el estado, `Permit #`, aprobación, vencimiento y costo.
- MP-21: `MOT & Packages (Prototype)` (`2866571577085828`, 34): filas `MOT` (trámites `KMV-MOT`) y `Package` (proyectos o permisos con `Prepare Packages`). Lo trabaja la persona de MOT y paquetes. Vuelven el estado, `Custom MOT` y `TYPICAL MOT`.
- MP-21b: `Row Type` en `MOT & Packages` dice si la fila es un paquete o un MOT. En la 1.0 no hacía falta: un paquete era la fila del proyecto (madre) con `Prepare Packages` y un MOT era una hija `KMV-MOT`; `Project Status` sólo ayudaba (fase 3 en paquetes, 5 y 6 en MOT). Esta hoja es plana (sin madres ni hijas) y no trae `Type of Project`, y el estado no alcanza: una fila nace sin estado, `CANCELLED` y `COMPLETE` existen en las dos, y el estado cambia mientras lo que es la fila no. La escribe el servicio al crear la fila (`Package` si viene de un proyecto con `Prepare Packages` o de un permiso con su propio paquete; `MOT` si viene de una hija `KMV-MOT`) y está bloqueada: nadie la llena. Sirve para tres cosas: el panel de la vista `MOT & PACKAGES` muestra sólo los campos de paquetes o sólo los de MOT (`Field Logic`, que sólo acepta listas como condición: por eso es una lista de dos valores); los contadores de días quedan vacíos donde no corresponden (`Prepare Packages # Days` en `MOT`, `Design MOT # Days` en `Package`); y las automatizaciones que al crear la fila registran la fecha de pedido y avisan (AUTOMATIZACIONES AU-30 a AU-33).
- MP-22: `Records Requests (Prototype)` (`3471473697312644`, 23): una fila por pedido de Records a una agencia (cuando el trámite tiene `Records Needed` o `Records Owner`, y `Agency`). La maestra lee de aquí `Records Status`.
- MP-23: `Billing (Prototype)` (`4630718656499588`, 43): una fila por cada fila de la maestra con ID. Facturación lleva las facturas; vuelve `Invoice Status`. El metraje se ve aquí y facturación lo puede corregir (pasa a la maestra con aviso, MP-70).
- MP-24: `Design Tickets (Prototype)` (`263146012102532`, 14): una fila por proyecto con `DT Owner`. Vuelven `Design Ticket` y `Mile Post`.

## Listas de apoyo (carpeta `Producto/List Tools`)

- MP-30: `Customer List` (`8537217871073156`): clientes y sus contactos; de aquí sale `Client Access` (fórmula de la maestra).
- MP-31: `Project Status List` (`6541648290074500`): cada estado con su fase y si cierra el proyecto; de aquí salen `Phase` y `Closed` (fórmula de la maestra).
- MP-32: `Contact List` (`8285254227021700`): directorio de personas (nombre, correo, equipos, activo). Lo usa el servicio para el aviso de metraje (`Footage Alerts`) y, cuando se encienda, para las listas de asignación (`APP_CONTACT_OPTIONS_ENABLED`, hoy apagado; K2-89).
- MP-33: `Project List` y `Designers List` son de la 1.0: la 2.0 no las usa.

## Vistas (Dynamic Views) de la 2.0

Nueve vistas, todas sobre su hoja salvo diseño (sobre un reporte). Hoy sólo las ve el dueño, salvo MOT y Records; con quién se comparte cada una lo decide el usuario.

- MP-40: `PROJECT KMV 2.0 - PROJECTS` (maestra, filtro `Projects`): la coordinadora crea y edita proyectos. Sin restricción por usuario; permite agregar filas.
- MP-41: `PROJECT KMV 2.0 - PERMITS` (maestra, filtro `Permits`): la coordinadora crea trámites con `Parent Project` y `Agency`; permite agregar filas.
- MP-42: `PROJECT KMV 2.0 - DESIGN` (reporte `KMV 2.0 | Design Projects`): diseño ve sus proyectos (restringida por `Designers`) y, junto al estado, si ya llegaron los Records o ya está todo hecho (`Records Status`, `Complete` con todo en `Record Box`), el `Design Ticket` y el `Mile Post`.
- MP-43: `PROJECT KMV 2.0 - PERMITS TEAM` (`Permits`): el equipo de permisos ve sus trámites (restringida por `Permitting Team`); el panel muestra sólo la revisión que toca.
- MP-44: `PROJECT KMV 2.0 - MOT & PACKAGES` (`MOT & Packages`): la persona de MOT y paquetes ve todo (sin restricción).
- MP-45: `PROJECT KMV 2.0 - RECORDS` (`Records Requests`): el equipo de Records ve sus pedidos (restringida por `Records Owner`).
- MP-46: `PROJECT KMV 2.0 - BILLING` (`Billing`): facturación ve todo (sin restricción).
- MP-47: `PROJECT KMV 2.0 - DESIGN TICKETS` (`Design Tickets`): cada `DT Owner` ve los suyos.
- MP-48: `PROJECT KMV 2.0 - CUSTOMERS` (maestra): cada cliente ve sus proyectos, también los cerrados (restringida por `Client Access`); sólo lectura.
- MP-49: la vista vacía `KMV 2.0 | Records` se borró el 2026-11-23 a pedido del usuario: la de Records es MP-45.

## Reportes (carpeta `PROJECT KMV 2.0 - Prototype/Reports`)

- MP-50: en uso por una vista: `KMV 2.0 | Design Projects` (`3039907867217796`, vista de diseño).
- MP-51: de consulta, sin vista: `KMV 2.0 | Records`, `KMV 2.0 | Coordinator`, `KMV 2.0 | Permits`, `KMV 2.0 | MOT & Packages`, `KMV 2.0 | Billing`, `KMV 2.0 | Design Tickets`. Las vistas van directo sobre sus hojas (K2-60), así que estos se pueden dejar o borrar.
- MP-52: los de `Producto/Reports` (`Permitting`, `Invoices`, `KMV - Customers` y otros) son de la 1.0.

## Automatizaciones (Smartsheet)

29 en las 6 hojas, todas apagadas hasta probarlas de a una. Lista completa en `../AUTOMATIZACIONES_2.0_RESUMEN.md`.

- MP-53: avisos de asignación (`DV | ...`): llegan a quien recibe un trabajo, con el enlace a su vista: diseñadores, equipo de permisos, persona de MOT y paquetes, Records y `DT Owner`.
- MP-54: alertas para el ingeniero: QC pendiente, QC demorado más de 1 día, factura lista para enviar y facturas enviadas sin cobrar (lunes).
- MP-55: automáticas sin correo: ingeniero y topógrafo por defecto, fecha de `QC IN`, fechas de pedido de paquete y MOT, fechas de `LT Records`.
- MP-56: aviso al cliente cuando cambia su estado (sólo para producción) e ideas apagadas sin decidir.
- MP-57: las automatizaciones no dependen del servicio, pero varias se disparan con lo que él escribe: las filas nuevas de las hojas de equipo, los estados que vuelven y el ID.

## Qué depende del servicio y qué no

- MP-58: depende del servicio (si está apagado, se atrasa): el ID de cada proyecto, que el trámite quede bajo su proyecto, las filas de las hojas de equipo y sus datos copiados, los estados y resultados que vuelven a la maestra, `Obs`, las listas de `Parent Project` y `Linked Tracking`, el metraje corregido por facturación y su aviso.
- MP-59: no depende del servicio (funciona siempre): las vistas, el formato de colores, las fórmulas (días, fase, cerrado, acceso del cliente, `Records Status`, `Revision Stage`), las automatizaciones de Smartsheet y lo que cada persona escribe en su vista.
