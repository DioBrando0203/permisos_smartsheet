# Dynamic Views anteriores a la 2.0 (VA-xx)

Estado 2026-11-22. Registro de las Dynamic Views de prueba que armamos antes de la 2.0 (del 2026-10-20 al 2026-11-13): qué tenía cada una, cómo funcionaba y qué aprendimos. Se documentan antes de borrarlas para poder rearmarlas si hace falta. La guía vigente es `../VISTAS_KMV_2.0.md` (VK-xx).

Fuente: lectura con el navegador de la cuenta dueña (la API pública no lee Dynamic Views; la aplicación de Dynamic View sí responde `GET /dynamicview/api/views/{id}?include=config,shares,form,filters` y `.../sourcemetadata`) y automatizaciones por API, sólo GET. Sin correos ni nombres de personas: las personas se cuentan.

## Archivos

- `README.md`: lo común a todas, grupos, avisos, qué se borró y qué quedó (VA-00 a VA-09).
- `others_2026.md`: tres vistas sobre la hoja de producción `8. Others - Engineering Plan 2026` (VA-10 a VA-19).
- `blue_stream.md`: dos vistas sobre la copia de Blue Stream 2026 en Pruebas (VA-20 a VA-29).
- `crown_castle.md`: dos vistas sobre la hoja de producción `8. Crown Castle Fiber - Engineering Plan 2026` (VA-30 a VA-39).
- `kmv_presentable.md`: cinco vistas sobre `PROJECT KMV` (la maestra anterior a la 1.0.0, en Pruebas) (VA-40 a VA-49).
- `kmv_1_0_0.md`: la vista sobre `PROJECT KMV 1.0.0` y los avisos de esa hoja (VA-50 a VA-59).
- `piloto_tareas.md`: la primera vista piloto, sobre `Tareas (Piloto)` (VA-60 a VA-69).
- `kmv_2_0.md`: vistas de la 2.0 borradas a pedido del usuario, con lo que tenían (VA-70 a VA-79).

## Cómo funcionaban (común)

- VA-00: dónde se configura: `https://app.smartsheet.com/dynamicview/views/<id>/admin/basic`, pestañas `General`, `View Display`, `Details Panel` y `Sharing` (detalle de cada ajuste en `../VISTAS_KMV_2.0.md` VK-01 a VK-09).
- VA-01: todas eran de la cuenta dueña y sobre una hoja (salvo las de ejemplo); el origen no se puede cambiar después de crear la vista.
- VA-02: restricción por usuario (`Restrict view by current user`): cada persona veía sólo las filas donde su correo estaba en una columna de contacto. En las hojas 2026 y en `PROJECT KMV` la asignación tenía dos columnas por equipo: la de nombre (lista, la que llenaba la coordinadora) y otra de contacto con el correo (`Email Designer1`, `Email Designer2`, `Email Permitting`, `Email Permitting Team`; en la copia de Blue Stream, `Correo Designer1` y `Correo Designer2`). La vista y el aviso usaban la de correo. En la 2.0 una sola columna de contacto hace las dos cosas (`../AUTOMATIZACIONES_KMV_2.0.md` AU-00j).
- VA-03: `Designer2` era en la práctica la persona de Records o de permisos según la hoja: la vista de Records se restringía por `Email Designer2`. En la 2.0 eso es `Records Owner` y `Permitting Team`.
- VA-04: comentarios: se mostraban en casi todas; en las de diseño no se podían agregar y en las de permisos y Records sí. El aviso de comentario iba a la hoja de origen (`SOURCE_SHEET`).
- VA-05: `Export to .csv`: sólo en `KMV - CUSTOMERS`, `KMV - RECORDS DV` y `KMV - PERMITS`.
- VA-06: ninguna usaba `Field Logic` (reglas del panel): un solo panel por vista. La 2.0 sí separa paneles por tipo.
- VA-07: grupos de Smartsheet usados para compartir (siguen existiendo; no se tocan): `DV Designers` (7 miembros, 3 con correo personal), `DV Permit Team` (7, todos de empresa), `Dynamic View - Internal` (4) y `Dynamic View - External` (4, 3 con correo personal). Compartir con un grupo da acceso a la vista, no a la hoja.
- VA-08: avisos: automatizaciones `DV | ...` con `Alert someone` a la columna de correo y el enlace a la vista en el mensaje (`https://app.smartsheet.com/dynamicview/views/<id>`). Si la vista se borra, el enlace del aviso queda roto: antes de borrar se buscaron enlaces en las automatizaciones de las 140 hojas y en los 50 dashboards de la cuenta.

## Qué se borró y qué quedó (2026-11-22)

- VA-08b (2026-11-23, pedido del usuario): todo lo que se borre se documenta antes en esta carpeta, con lo que tenía, como historial.
- VA-08c (2026-11-23): además se borraron, a pedido del usuario, `KMV - CUSTOMERS` (VA-45, reemplazada por `PROJECT KMV 2.0 - CUSTOMERS`) y la vista vacía de la 2.0 `KMV 2.0 | Records` (VA-70). Ese mismo día, también a pedido del usuario, se borraron `KMV - Designers` (VA-41) y las tres de `8. Others - Engineering Plan 2026` (VA-10 a VA-12); los tres avisos de esa hoja de producción siguen encendidos con el enlace roto hasta que el usuario los apague (VA-15). Quedan sólo las 9 vistas de la 2.0 y las de ejemplo fuera de Pruebas.

- VA-09: decisión del usuario: documentar y borrar las vistas de prueba anteriores a la 2.0, y dejar por ahora todo lo que tenga que ver con la 2.0. Regla del usuario (2026-11-22): no se borra ninguna vista que pertenezca a la 2.0; excepción pedida por el usuario el 2026-11-23: la vista vacía `KMV 2.0 | Records` (`../VISTAS_KMV_2.0.md` VK-00t6).
  - Borradas el 2026-11-22 a las 20:47 (comprobado: quedan 17 vistas de 26): `PROJECT KMV 1.0.0` (VA-50), `Permisos (piloto pruebas)` (VA-60), `KMV - PERMITS` (VA-42), `KMV - RECORDS DV` (VA-43), `KMV - MP/DT DV` (VA-44), `Blue Stream - Designers` (VA-20), `Blue Stream Permit` (VA-21), `8. Crown Castle Fiber - Engineering Plan 2026` (VA-30) y `8. Crown Castle Fiber - Engineering Plan 2026 V` (VA-31).
  - Se quedan por la 2.0: `KMV - Designers` (VA-41) y `KMV - CUSTOMERS` (VA-45): las automatizaciones `DV | New Project`, `DV | New Project (ID assigned)` y `Client | Status Update` de la maestra 2.0 (apagadas) todavía enlazan a ellas. Se borran cuando esos avisos apunten a `KMV 2.0 | Design Projects` y a la vista de clientes de la 2.0 (`../KMV_2.0.md` K2-87b, `../AUTOMATIZACIONES_KMV_2.0.md` AU-00e). Actualización 2026-11-22 21:50: esos tres avisos ya enlazan a las vistas de la 2.0 (`PROJECT KMV 2.0 - DESIGN` y `PROJECT KMV 2.0 - CUSTOMERS`), así que estas dos se pueden borrar cuando el usuario lo diga.
  - Esperan confirmación del usuario: las tres de `8. Others - Engineering Plan 2026` (VA-10 a VA-12): tres automatizaciones activas de esa hoja de producción envían hoy su enlace, y están compartidas con `DV Designers` o `DV Permit Team` y con personas.
  - Fuera de este pedido (siguen): `Dynamic View Sample` (tres), `Project List Report - DYNAMIC VIEW SAMPLE` y `TEST - Report - Customer1+Customer2`, sobre hojas y reportes de ejemplo fuera de Pruebas.
  - Las hojas de origen no se borran (`PROJECT KMV`, `PROJECT KMV 1.0.0`, `Tareas (Piloto)`, la copia de Blue Stream); sus automatizaciones que enlazan a vistas borradas quedan con el enlace roto (VA-49, VA-59). Desde el 2026-11-22 21:50 esos avisos están apagados, junto con los demás avisos de Pruebas fuera de la 2.0 (`../AUTOMATIZACIONES_KMV_2.0.md` AU-85).
