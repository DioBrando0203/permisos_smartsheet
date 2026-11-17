# KMV 2.0: estado actual

Versión vigente desde el 2026-11-16. Este documento es la fuente única del estado de la 2.0: qué hojas hay, qué hace cada quien, qué hace el servicio, qué falta y qué opino. Para el detalle de cada regla: SPEC-B18 (Records), SPEC-B19 (Billing), SPEC-B20 (hojas de proceso), SPEC-ID01 ID-51 a ID-54 (IDs, en `servicios/ids/SPEC.md`). Cómo armar las vistas: `VISTAS_KMV_2.0.md`. El historial de cómo se llegó aquí está en `REQUERIMIENTOS.md` PEN-54; la 1.0.0, en `HOJA_PROJECT_KMV.md` (ya no la procesa el servicio).

## La idea

- K2-01: la fila madre es el proyecto (datos, diseño, metraje y asignaciones); cada hija es un trámite según su `Type of Project`, y el trabajo de cada trámite vive en la hoja de su equipo. La coordinadora sólo crea filas en la maestra, desde vistas; cada equipo trabaja en su hoja, desde su vista; el servicio numera, indenta, copia y resume. Nadie escribe lo mismo dos veces.
- K2-02: Smartsheet sigue siendo la fuente de verdad (ADR-B15). Lo que se puede calcular con fórmulas lo calcula Smartsheet; el servicio sólo hace lo que Smartsheet no puede: numerar, mover filas bajo su proyecto y mantener filas en otras hojas.

## Hojas

Carpeta `Pruebas/Producto/PROJECT KMV 2.0 - Prototype` (prototipo; todo en Pruebas).

- K2-03: `PROJECT KMV 2.0 (Prototype)` (`1979884168761220`): maestra, 79 columnas, unas 6 329 filas por año (2026 proyecta unas 4 230: 67 %). Decir siempre cuántas columnas tiene tras cualquier cambio.
- K2-04: `Permits (Prototype)` (`3435959686483844`, 44 columnas): una fila por hija `KMV-Permit` o `KMV-Line` y por proyecto `KMV-Miscellaneous` (HP-16).
- K2-05: `MOT & Packages (Prototype)` (`2866571577085828`, 34): filas `MOT` (hijas `KMV-MOT`) y `Package` (madres con `Prepare Packages`).
- K2-06: `Records Requests (Prototype)` (`3471473697312644`, 23): una fila por pedido de Records.
- K2-07: `Billing (Prototype)` (`4630718656499588`, 43): una fila por cada fila de la maestra con ID.
- K2-08: `Design Tickets (Prototype)` (`263146012102532`, 14): una fila por proyecto con `DT Owner` (por revisar si hace falta).
- K2-09: todas las hojas hijas llevan `Linked Tracking` (copiada del proyecto, HP-17) y `Master Row` oculta (el vínculo con su fila de la maestra). En `Billing` y `Permits` la columna principal es `Primary` (fórmula con el ID) y `Tracking Project` es una columna normal, para que los reportes de varias hojas ordenen e intercalen por ID.

## IDs

- K2-10: formato `KMV-AA-NNNN` (`KMV-26-0001`): un contador por año, sin cliente; el cliente sigue siendo obligatorio para numerar. Una fila nueva muestra `Pending ID` y en un minuto recibe su número.
- K2-11: las hijas heredan el ID de su madre, aunque tengan otro cliente.
- K2-12: un trámite creado desde una vista queda de primer nivel: no gasta número; con `Parent Project` el servicio lo mueve bajo su proyecto y le da el ID de la madre.
- K2-13: `Parent Project` lista exactamente los proyectos actuales (los más nuevos primero); `Linked Tracking` suma los nuevos y conserva los de años anteriores. Las mantiene el servicio.

## Qué hace la coordinadora

- K2-20: proyecto (vista `PROJECTS`): `Type of Project` (`KMV-P` diseño o `KMV-Miscellaneous` permisos), `Customer`, `Date Received`, `Project Name`; asigna `Designers` y `Permitting Team`.
- K2-21: trámite (vista `PERMITS`): `Type of Project` (`KMV-Permit`, `KMV-Line` o `KMV-MOT`), `Parent Project`, `Agency`; `Permitting Team` si no es el del proyecto. Sin `Agency` el trámite no pasa a la hoja del equipo; si no requiere permiso nace en `NO PERMIT REQUIRED` y tampoco pasa.
- K2-22: Records: `Records Needed` o `Records Owner` en la fila del trámite (Records siempre se pide a una agencia).
- K2-23: paquetes: `Prepare Packages` en el proyecto. Design Ticket: `DT Owner` en el proyecto.
- K2-24: cancelar: `CANCELLED` en la fila; nunca se borra. Se cancela también en la hoja del equipo.
- K2-24b: notas: siempre como conversación de la fila (`Comments` en la vista); nadie escribe en `Obs`, que el servicio llena con esas conversaciones (SPEC-B17) y queda bloqueada.
- K2-25: crea unas 2 filas por proyecto (en promedio 1,5 trámites); nunca crea filas en las otras hojas.

## Qué hace el servicio

- K2-30: IDs cada minuto; las hojas cada 30 segundos, en este orden: herencia, Records, `Billing`, `Permits`, `MOT & Packages`, `Design Tickets` y listas de proyectos.
- K2-31: herencia: una hija completa sus celdas vacías con las de su proyecto (`Customer`, `Project Name`, dirección, ciudad, condado, `CC System`, fechas, `LT`); nunca reemplaza.
- K2-32: `Permits` y `MOT & Packages`: fila cuando la hija tiene tipo, ID y `Agency` y no está cerrada; contexto del proyecto copiado y bloqueado (lo vacío en la hija se toma del proyecto); el estado del equipo (`Permit Status`, `MOT Status`) vuelve como `Project Status` de la hija, junto con `Permit #`, `Permit Approved`, `Permit Expires`, `Permit Fee`, `Custom MOT`, `TYPICAL MOT`; `CANCELLED` en la maestra se impone.
- K2-32b: los proyectos `KMV-Miscellaneous` también tienen fila en `Permits`; a la madre vuelven `Permit #`, `Permit Approved`, `Permit Expires` y `Permit Fee`, no el estado (HP-16). `Linked Tracking` va copiada en todas las hojas de equipo (HP-17).
- K2-33: Records: fila con `Records Needed` o `Records Owner` y `Agency`.
- K2-34: `Billing`: fila para toda fila con ID; metraje y cantidades copiados y bloqueados (los llena diseño en la maestra, facturación sólo los ve); `Invoice Status` vuelve a la maestra.
- K2-35: `Design Tickets`: fila al asignar `DT Owner`; `Design Ticket` y `Mile Post` vuelven a la maestra.
- K2-36: `Obs`: copia las conversaciones de cada fila de la maestra a su `Obs` (SPEC-B17, `APP_OBS_SYNC_ENABLED`).

## Qué calcula Smartsheet solo

- K2-40: `Tracking Project`, `Phase`, `Closed`, `Client Access`, los días (`... # Days`) y `Control Linked Tracking` (oculta) en la maestra.
- K2-41: `Records Status` en la maestra: por proyecto, `Received`, `No records` o `Pending (n/m received)`, leyendo la hoja de Records (tarda 15 a 30 segundos).
- K2-42: `Revision Stage` en `Permits`: `No revision`, `1st Revision` o `2nd Revision`, para mostrar cada revisión sólo cuando hace falta.

## Columnas de la maestra 2.0 (79)

- K2-50: identificación: `Primary` (fórmula `KMV-P`), `Type of Project`, `Tracking Project`, `Linked Tracking`, `Parent Project`.
- K2-51: proyecto: `Priority`, `CC System`, `Task`, `Project Name`, `Project Address`, `City`, `County`, `Customer`, `Client Access`, `Date Received`, `Project Status`, `Phase`, `Closed`, `LT`, `Process # Days`.
- K2-52: diseño: `Drawing Due Date`, `Project # Days`, `QC IN`, `QC OUT`, `QC # Days`, `Survey Completed`, `Survey Check`, `Design Completed`, `PM Approval Date`, `PM Approval Days`, `Design Completed Days`, metraje (`Total Footage`, `UG`, `UG + Profile`, `ISP`, `Aerial`), `Sonde Request`, `Sonde Received`, `Sonde # Days`, `Asbuilt received - Bore Log`, `As-Built Complete Date`, `As-built # Days`.
- K2-53: asignación y pedidos: `Designers`, `Permitting Team`, `Surveyor`, `Engineer`, `Construction Manager`, `Contractor`, `Agency`, `Records Needed`, `Records Owner`, `DT Owner`, `Prepare Packages`, `Stamp & Seal`, `Stamp And Signatures #`.
- K2-54: cantidades: `Custom MOT`, `TYPICAL MOT`, `Survey Certified`, `Additional Site Survey`, `Tone Locating`, `Sonde FTG`, `GPR`.
- K2-55: resúmenes que escribe el servicio o una fórmula (bloqueados): `Permit #`, `Permit Approved`, `Permit Expires`, `Permit Fee`, `Design Ticket`, `Mile Post`, `Invoice Status`, `Records Status`, `Obs`.
- K2-56: técnicas y de sistema (ocultas o no se muestran): `Customer Code`, `Year`, `Row Order`, `Stable Tracking Project`, `Row Level`, `Control Linked Tracking`, `Modified`, `Modified By`.

## Reportes y vistas

- K2-60: regla (2026-11-17 15:27, decisión del usuario): todas las vistas van directo sobre su hoja; ninguna usa reporte. Las hojas de equipo ya traen copiados los datos del proyecto. Lista y configuración en `VISTAS_KMV_2.0.md` (VK-00a a VK-00h).
- K2-61: el equipo de permisos tiene una sola vista, `PERMITS TEAM` sobre `Permits`: sus permisos, líneas y proyectos `KMV-Miscellaneous` (HP-16).
- K2-62: filtros compartidos de la maestra (los crea el usuario en la hoja): `Projects` y `Permits`.
- K2-63: los reportes de la carpeta `Reports` (`5430691564414852`) ya no se usan para las vistas; quedan de consulta o se pueden borrar. La API no edita reportes existentes.

## Configuración

- K2-70: `backend/.env` apunta a la 2.0: `IDS_MASTER_SHEET_ID=1979884168761220`, `IDS_PROJECT_FORMAT=year`, `IDS_PROJECT_OPTIONS_ENABLED`, `APP_INHERIT_ENABLED`, hojas de Records, Billing, `Permits`, `MOT & Packages` y `Design Tickets` activas, catálogo `Project List` sin sincronizar. Lista completa en SPEC-B20 HP-10 y `.env.example`.
- K2-71: volver a la 1.0.0: los valores anteriores están comentados al final del `.env`; la maestra 1.0.0 no tiene metraje (habría que recrearlo o revertir SPEC-B19 FH-05b).
- K2-72: un cambio de código o de `.env` exige reiniciar el backend (sin `--reload` no carga cambios). Nunca correr una pasada manual con el backend encendido: dos procesos a la vez pueden duplicar filas.

## Pendientes, en orden

- K2-80: hecho (2026-11-17 15:44): backend reiniciado con el último código; vistas `PROJECTS`, `PERMITS` y `PERMITS TEAM` armadas por el usuario (VISTAS VK-00t).
- K2-81: hecho (2026-11-17 15:48): filtros compartidos `Projects` y `Permits` en la maestra; falta elegirlos en cada vista.
- K2-82: filtros compartidos `Projects` y `Permits` en la maestra; armar las vistas (guía `VISTAS_KMV_2.0.md`).
- K2-83: formato condicional de `CANCELLED` (gris y tachado) en `Permits` y `MOT & Packages`.
- K2-84: probar el flujo completo con las vistas: proyecto, trámite con `Parent Project` y `Agency`, estado del equipo de vuelta, cancelación.
- K2-85: código: mover la fila a la otra hoja cuando cambia el tipo (SPEC-B20 HP-08), la única regla decidida que falta.
- K2-85b (2026-11-17 15:28, hallazgo; el usuario: no se puede perder nada): `Obs` sólo junta las conversaciones de la maestra (SPEC-B17, `pilot.SHEETS`). Lo que un equipo comenta en su hoja (`Permits`, `MOT & Packages`, Records, `Billing`, `Design Tickets`) queda en esa fila, no se pierde, pero no llega al `Obs` de su fila en la maestra. Pasa igual con vistas sobre hoja o sobre reporte (el comentario se guarda en la fila de origen). Arreglo en el servicio: juntar también los comentarios de las hojas de equipo en el `Obs` de su fila de la maestra, por `Master Row`. Hasta entonces, la vista sobre la hoja no pierde nada frente al reporte.
- K2-85c (2026-11-17 16:27, historial 2026): la casilla `Prepare Packages` y `Prepare Packages Request` las pone la coordinadora; `3. Packages Completed` lo ponía una automatización; la persona de MOT llena QC y Completed de paquetes, diseño de MOT y cantidades. `Row Type` de `MOT & Packages` pasó a lista (`MOT`, `Package`) para separar paneles. Automatizaciones sugeridas en VISTAS VK-35b.
- K2-86: avisos y automatizaciones de la 2.0 (asignación de `Permitting Team`, `Records Owner`, `DT Owner`).
- K2-87: decidir si `Design Tickets` se queda; `Row Type` de `MOT & Packages` como lista si se quiere separar paneles.
- K2-88: plan de paso a producción (ver mi opinión, K2-93).

## Mi opinión (Claude)

- K2-90: el modelo funciona porque cada dato tiene un solo dueño y un solo lugar donde se escribe. Lo que más lo puede romper es lo mismo que rompía la 1.0: columnas nuevas "por si acaso" y gente escribiendo en celdas copiadas. Antes de agregar una columna, preguntar quién la llena y dónde la ven los demás; si la respuesta es "ya está en otra hoja", es una copia y va bloqueada.
- K2-91: el punto débil es el servicio: si está apagado, nada se numera ni pasa a las hojas de los equipos (las vistas siguen funcionando, pero se acumula `Pending ID`). En producción tiene que correr en un servidor que no dependa de que alguien prenda una máquina, y `Pending ID` por más de unos minutos es la alarma.
- K2-92: no movería diseño fuera de la maestra mientras la capacidad alcance (hoy 67 %): ganaría columnas a cambio de más piezas que sincronizar. Si un año la maestra pasa del 85 %, entonces sí: hoja `Design` con el mismo mecanismo.
- K2-93: para producción empezaría limpio: la 2.0 para los proyectos nuevos de un año (o desde una fecha de corte), y lo anterior se queda donde está, enlazado por `Linked Tracking` (que ya acepta IDs con cliente). Migrar 2026 a mitad de año mezcla dos formatos de ID y dos formas de trabajar en la misma hoja; no vale el riesgo.
- K2-94: antes de producción implementaría el cambio de tipo (K2-85) y una prueba con las vistas reales de dos o tres personas por una semana. Las vistas cortas (pocas columnas, paneles por campos con `Field Logic`) son la diferencia entre que la gente las use o vuelva a pedir la hoja completa.
- K2-95: `Design Tickets` me parece prescindible: dos campos que la coordinadora o el `DT Owner` podrían llenar en el proyecto desde su vista. La dejaría apagada salvo que el `DT Owner` sea alguien que no debe ver nada más.
