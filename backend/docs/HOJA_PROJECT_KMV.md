# Estado de la hoja de trabajo PROJECT KMV

Foto del 2026-11-12 18:45 -05:00, leída por API (sólo GET) y cruzada con las specs y decisiones. Sin correos ni nombres de personas. Para el porqué de cada decisión, ver los PEN y specs citados; para el detalle cronológico, `bitacora/BITACORA.md`. Al cambiar la hoja o el servicio, actualizar este archivo.

## Ubicación y hojas relacionadas

- HK-01: PROJECT KMV, id `5254686035890052` (antes "Presentable"), workspace Pruebas (`7965022790936452`), carpeta `Producto`. Maestra de prueba con todos los clientes. Decidido (PEN-45): en producción, una maestra por año.
- HK-02: `Producto/List Tools` (catálogos que la hoja usa por referencias o desplegables vinculados):
  - Contact List `8285254227021700`: `Nombre`, `Correo` (contacto), `Activo`; directorio del equipo para los correos de diseñadores y permisos.
  - Project List `8048198976491396` (antes "Catálogo de Proyectos (Piloto)"): `Tracking Project`, `Customer Code`, `Customer`, `Company`, `Origin`; origen del desplegable `Linked Tracking`; la escribe el servicio (SPEC-B16) y nunca borra filas.
  - Customer List `8537217871073156`: `Customer`, `Code`, `Client Contacts` (contactos múltiples), `Active`, `Notes`, `Check`; 11 clientes.
  - Project Status List `6541648290074500` (antes "Project Status Catalog"): `Status`, `Phase`, `Closed`; origen del desplegable `Project Status` (PEN-27).
- HK-03: `Producto/Reports`: All Records Request, Invoices, MOT y Paquetes, Permitting y KMV - Customers (`4804688689188740`, fuente sólo PROJECT KMV, 14 columnas del tracker de cliente).
- HK-04: Dynamic Views (la API pública no las lee; lo que se sabe viene del usuario y de las automatizaciones): vista de clientes "KMV - CUSTOMERS" `70132910-6338-4f25-a814-d15aff143bbe`; vistas del equipo enlazadas en los avisos: Designer1 `482e8b5d-cf2f-4330-9d41-faba46552fdb`, Designer2 `b21c185f-b7d4-4b25-91b7-f117a9238de5`, Permitting `fef91195-cab5-4495-8987-359d946483cc`.
- HK-05: Otras carpetas de Pruebas: `Normalizacion de Datos - Piloto` (piloto anterior, reportes PILOTO y hoja Forms) y `Testing` (copias de hojas y reportes reales). Fuera de Pruebas todo es sólo lectura (por ejemplo, el reporte original "Tracker 2026 - KMV").

## Estructura: madres e hijas

- HK-06: Cada fila de primer nivel (madre) es un proyecto y tiene su Tracking Project. Las hijas (permisos o tareas) van indentadas debajo y llevan el mismo Tracking Project que su madre (SPEC-ID01 ID-38).
- HK-07: Foto de datos: 14 filas, 8 madres y 6 hijas. Madres: `KMV-BS-26-001` (1 hija), `KMV-CC-26-001` (1 hija), `KMV-CC-26-002` (2 hijas), `KMV-LP-26-001` (2 hijas), `KMV-CC-26-004`, `KMV-HC-26-001`, `KMV-BS-26-009` y `KMV-HC-26-002`. Todas son filas de prueba.
- HK-08: Flujo de uso: crear la madre con `Customer` y `Date Received`; aparece `Pending ID` y en 5 a 15 s el servicio le da el siguiente número libre de ese cliente y año. Las hijas se insertan debajo y se indentan; muestran el ID de su madre. Si la hoja no se refresca sola, recargar.

## Columnas clave

- HK-09: `Tracking Project` (índice 14, fórmula, sólo muestra): madre con Stable ID que corresponde, ese ID; madre sin Stable ID con cliente y año, `Pending ID`; madre cuyo Stable ID es de otro cliente o es copia de otra madre (mismo Stable ID y `Row Order` mayor), `Pending ID`; hija con cliente vacío o igual al de su madre, el `Tracking Project` de su madre; hija de otro cliente, `Pending ID` (SPEC-ID01 ID-48 e ID-49). Fórmula vigente: `=IF([Row Level]@row > 0, IF(OR(ISBLANK([Customer Code]@row), [Customer Code]@row = INDEX(ANCESTORS([Customer Code]@row), 1)), INDEX(ANCESTORS([Tracking Project]@row), 1), "Pending ID"), IF(ISBLANK([Stable Tracking Project]@row), IF(AND(NOT(ISBLANK([Customer Code]@row)), ISNUMBER(Year@row)), "Pending ID", ""), IF(OR(AND(NOT(ISBLANK([Customer Code]@row)), NOT(CONTAINS("-" + [Customer Code]@row + "-", [Stable Tracking Project]@row))), COUNTIFS([Stable Tracking Project]:[Stable Tracking Project], [Stable Tracking Project]@row, [Row Level]:[Row Level], 0, [Row Order]:[Row Order], VALUE(@cell) < VALUE([Row Order]@row)) > 0), "Pending ID", [Stable Tracking Project]@row)))`. Las fórmulas anteriores están en SPEC-ID01 ID-48 e ID-49.
- HK-10: `Stable Tracking Project` (134, oculta y bloqueada): la escribe sólo el servicio; es el ID real.
- HK-11: Columnas auxiliares ocultas: `Customer Code` (131, `=IFERROR(LEFT(Customer@row, FIND("-", Customer@row) - 1), "")`), `Year` (132, año de `Date Received`), `Row Order` (133, autonumérico de sistema), `Row Level` (137, nivel de jerarquía), `Project Number` (136) y `Frozen Number` (135). Las dos últimas ya no intervienen en `Tracking Project`.
- HK-12: `Linked Tracking` (15): desplegable vinculado a Project List (17 opciones, sin validación). `Control Linked Tracking` (138, fórmula): `OK`, `ERROR: SAME PROJECT`, `ERROR: DIFFERENT CUSTOMER` o `LEGACY: NOT LOADED`; un formato condicional pinta en rojo los errores.
- HK-13: `Customer` (20): desplegable de 11 clientes con validación. `Client Access` (21, contactos múltiples, fórmula): `=IFERROR(INDEX({Customer List Client Contacts}, MATCH(Customer@row, {Customer List Customer}, 0)), "")`; da a cada fila los contactos de su cliente para la vista de clientes y los avisos.
- HK-14: `Date Received` (22, fecha): define el año del ID.
- HK-15: `Project Status` (46): desplegable vinculado a Project Status List (60 estados con validación). `Phase` (47) y `Closed` (48) por fórmula desde ese catálogo (PEN-27).
- HK-16: `Obs` (55, texto): historial `MM.DD - texto`; el servicio antepone los comentarios nuevos de cada fila; un comentario que empieza con `**` abre una sección arriba; los que empiezan con `#interno` o `#internal` no se copian (SPEC-B17).
- HK-17: Equipo: `Designer1` (62), `Designer2` (63) y `Permitting Team` (67) son desplegables; `Email Designer1` (65), `Email Designer2` (66) y `Email Permitting` (68) toman el correo desde Contact List por fórmula.
- HK-18: Referencias entre hojas (8, todas en estado OK y por columna completa): `Directorio Correo`, `Directorio Nombre`, `Directorio Activo` (Contact List); `Project Status Catalog Phase`, `Project Status Catalog Status`, `Project Status Catalog Closed` (Project Status List; conservan el nombre anterior); `Customer List Customer` y `Customer List Client Contacts`.
- HK-19: Filtros: `Open` (compartido, `Closed` sin marcar) y `Filter By Costumer` (personal del usuario).
- HK-20: Capacidad: 140 columnas, unas 3 571 filas como máximo por hoja (500 000 celdas). Medido el 2026-11-12: Crown Castle y Blue Stream suman 3 656 filas en 2025 y van 3 527 en 2026 (proyección 4 074), así que un año completo no entra con 140 columnas. Análisis de columnas a quitar en PEN-45. La cuenta es Enterprise, pero pasar a hoja a gran escala (1 000 000 de celdas, sólo vista de tabla) desactiva grid, automatizaciones, app móvil y los endpoints Get columns y Get row que usa el servicio: se descarta mientras Smartsheet no los admita (PEN-45).

## Automatizaciones de la hoja

- HK-21: `Client | Status Update` (activa, id `1825411349931908`): cuando una fila existente cambia `Project Status` a uno de 21 estados (los 19 del tracker de cliente que existen en el desplegable, más `IN PERMITTING` y `COMPLETE`) y `Client Access` no está vacío, envía a esos contactos un correo cordial en inglés: asunto `Project Update – {Tracking Project}: {Project Status}`, enlace a la vista de clientes y 10 columnas, sin adjuntos ni comentarios. Falta el primer envío real (PEN-44).
- HK-22: `DV | New Task Designer1` (activa): al cambiar `Designer1`, correo a `Email Designer1`; asunto `New Task: {Tracking Project} – {Project Name}`.
- HK-23: `DV | New Task Designer2` (activa): al cambiar `Designer2`, correo a `Email Designer2`; asunto con `Tracking Project`, `Project Name` y `Agency`.
- HK-24: `DV | New Task Permitting Team` (activa): al cambiar `Permitting Team`, correo a `Email Permitting`. Corregida el 2026-11-12: antes se disparaba con `Designer1`.
- HK-25: `Auto | LT Records al llenar Record ID` y `Auto | LT Records al cambiar Records Status` (activas): registran la fecha en `LT Records`. Inactivas: `Alertas`, `alert` y `Auto | LT on any change`.

## Lo que hace el servicio sobre la hoja

- HK-26: El backend corre en el equipo Linux del usuario (B-16), puerto 8710, y lo enciende el usuario. Barreras activas en `.env`: `APP_READ_ONLY=false`, `IDS_MONITOR_ENABLED`, `IDS_WRITES_ENABLED`, `IDS_TRANSITION_APPROVED`, `IDS_PROCESSOR_WRITES_ENABLED`, `IDS_CUSTOMER_CHANGE_ENABLED` y `APP_OBS_SYNC_ENABLED`, todas en verdadero; ciclo completo cada 60 s y consulta de versión cada 5 s (ID-43). Sólo escribe en Pruebas.
- HK-27: IDs (servicios/ids/SPEC.md): una madre recibe el siguiente número libre de su cliente y año, que nunca se reutiliza ni se baja (ID-32); una madre copiada recibe otro número (ID-42); si cambia el cliente de una madre, su ID se retira y recibe uno nuevo del cliente actual, también al volver al cliente original (ID-44); una hija de otro cliente sale de la jerarquía, pierde el ID heredado y recibe su propio número (ID-45); las hijas siguen a su madre cuando ella cambia de cliente (ID-46); una hija con otro ID toma el de su madre (ID-47); los `Linked Tracking` que apuntaban al ID anterior se actualizan solos.
- HK-28: Project List se sincroniza al final de cada ciclo (SPEC-B16 LB-06): agrega los IDs confirmados y nunca borra, así que los IDs retirados siguen como opción del desplegable.
- HK-29: Obs se actualiza al final de cada ciclo, como máximo una vez cada 30 s y hasta 20 filas por pasada (SPEC-B17).
- HK-30: Nada técnico se escribe en la hoja. El rastro queda en PostgreSQL (`galp_servicios`): `asignacion_id`, `secuencia_id`, `auditoria_id` (acciones `inicializado`, `reservado`, `confirmado`, `retirado`), `id_retirado` y `obs_comentario`; migraciones 001 a 005 aplicadas.
- HK-31: Números ya consumidos que no se ven en la hoja: Blue Stream 002 a 007 (filas borradas), 008 y 010 (retirados por cambio de cliente); Crown Castle 003 (fila borrada). Por eso el siguiente de Blue Stream es 011 y el de Crown Castle 005.

## Separación por cliente (PEN-44)

- HK-32: Vista de clientes: una sola Dynamic View para todos; cada persona ve sólo las filas donde figura en `Client Access` (restricción por usuario actual), sin el filtro `Open`: el cliente ve también lo cerrado (decisión del usuario). La configuración en la vista la hace el usuario; falta confirmarla y probar con una cuenta que no sea la dueña. Cada persona entra con una cuenta de Smartsheet con ese correo.
- HK-33: Contactos cargados (de prueba) en Customer List para Blue Stream, Crown Castle y Hotwire; Lightpath sin contactos, por eso sus filas no tienen `Client Access`.
- HK-34: Excel para clientes: un solo reporte, KMV - Customers. En cada envío se cambia `Customer` en Filter Criteria, se revisan las filas y se envía con File > Send as Attachment (Excel). Un envío programado por cliente exige un reporte propio. No se comparte el reporte con clientes: verían datos sólo con acceso a la hoja.

## Incoherencias de datos conocidas (no las corrige el servicio)

- HK-35: Fila 10, hija de `KMV-LP-26-001` ("PRUEBA 2"): `Linked Tracking` apunta a `KMV-BS-26-001` (otro cliente, en rojo) y no tiene `Date Received`.
- HK-36: `KMV-LP-26-001` no tiene `Project Name`.
- HK-37: Hay hijas con estados de madre (`COMPLETE`, `IN PROGRESS`) y quedan sin `Phase`; los estados en mayúsculas no tienen `Phase` en el catálogo (PEN-27, PEN-43).

## Pendientes ligados a la hoja

- HK-38: PEN-44: configurar y probar la vista de clientes con otra cuenta; primer envío real de `Client | Status Update`.
- HK-39: PEN-27: aprobación de la clasificación de estados, `Phase` de los estados en mayúsculas y reportes filtrados por `Closed`.
- HK-40: PEN-43: estados por equipo en el desplegable (falta decisión). PEN-45: decidir qué columnas quitar (11 sin uso real, 11 de uso mínimo y 6 nuevas por confirmar) y luego planificar las maestras por año (creación anual, ID Manager con varias hojas, vistas y reportes por año).
- HK-41: Todo está en git en `main`: código de PEN-46 y PEN-47 en `57b7191`, este archivo en `97f513a` y el análisis de columnas en `9ad8a7e`. El asistente hace commit al terminar cada tarea y el usuario hace push.
