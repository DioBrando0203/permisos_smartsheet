# El servicio (API) y el flujo de un proyecto (MP-60 a MP-99)

Estado 2026-11-23. Qué hace el servicio con la API de Smartsheet, cómo corre, qué pasa si se apaga y cómo avanza un proyecto de punta a punta, diciendo en cada paso quién lo hace: una persona, Smartsheet solo o el servicio. Sin nombres de personas: se nombran por su rol.

## Qué es el servicio

- MP-60: un programa (backend en Python) que habla con Smartsheet por su API con el token de un administrador de la cuenta. Es lo único de la 2.0 que usa la API: las vistas, las fórmulas, los colores y las automatizaciones son de Smartsheet y no la usan.
- MP-61: dónde corre: hoy en la PC Linux de la oficina, encendido todo el día; más adelante en Railway o AWS (`../KMV_2.0.md` K2-98). Siempre una sola copia: dos a la vez numerarían por separado.
- MP-62: qué guarda aparte: en PostgreSQL, los contadores de IDs, qué ID tiene cada fila, la auditoría de cada escritura y qué conversaciones ya copió a `Obs`. En las hojas no deja nada técnico.
- MP-63: dónde puede escribir: sólo en hojas del workspace `Pruebas` y sólo con las barreras de escritura encendidas en su configuración (`backend/.env`, donde vive el token).

## Qué hace con la API

- MP-64: numera: cada proyecto nuevo recibe `KMV-AA-NNNN` (un contador por año); mientras tanto la fila muestra `Pending ID`. Los trámites heredan el ID de su proyecto.
- MP-65: ordena: un trámite creado desde la vista `PERMITS` con `Parent Project` pasa a estar debajo de su proyecto.
- MP-66: hereda: un trámite completa sus celdas vacías con las de su proyecto (cliente, nombre, dirección, fechas, `LT`); nunca reemplaza lo escrito.
- MP-67: reparte: crea y mantiene la fila de cada trámite en la hoja de su equipo (`Permits`, `MOT & Packages`, Records, `Billing`, `Design Tickets`) con los datos del proyecto copiados y bloqueados; si el proyecto cambia, actualiza la copia.
- MP-68: devuelve: lo que cada equipo resuelve vuelve a la maestra: estado del trámite, `Permit #`, aprobación, vencimiento y costo, `Custom MOT` y `TYPICAL MOT`, `Design Ticket` y `Mile Post`, `Invoice Status`. `CANCELLED` en la maestra se impone en la hoja del equipo.
- MP-69: mantiene las listas: `Parent Project` (proyectos actuales, los nuevos primero) y `Linked Tracking` (suma los nuevos y conserva los de años anteriores).
- MP-70: metraje: diseño lo llena en la maestra; si facturación lo corrige en `Billing`, el servicio lo pasa a la maestra y manda la fila con el valor anterior y el nuevo al diseñador del proyecto, a la persona de avisos de metraje y al ingeniero.
- MP-71: `Obs`: copia las conversaciones de cada fila de la maestra a su columna `Obs`, con fecha y autor; nadie escribe en `Obs` a mano.

## Cómo corre

- MP-72: mira si la maestra cambió consultando su versión cada 5 segundos; tras 2 minutos sin cambios, cada 30 segundos (noches y horas sin trabajo), y vuelve a 5 con el primer cambio.
- MP-73: un ciclo corre al menos cada 60 segundos, o antes si algo cambió. Primero el ID Manager (numerar, ordenar, heredar el ID; por tandas, un máximo de filas por ciclo). Después los pasos, en este orden: herencia, Records, `Billing`, metraje, `Permits`, `MOT & Packages`, `Design Tickets`, listas de proyectos, listas de asignación (apagado) y `Obs`.
- MP-74: cada paso corre como mucho cada 30 segundos y sólo si alguna de sus hojas cambió; igual corre cada 10 minutos por seguridad (`Obs`, cada 2). Si un paso falla, los demás siguen y el fallo queda en el registro.
- MP-75: consumo de la API: Smartsheet admite 300 llamadas por minuto por token; el servicio se frena solo en 250. Lee cada hoja en un solo pedido. Estimado con la maestra de fin de año: unas 15 por minuto sin trabajo y 30 a 60 en los picos (SPEC-B21).
- MP-76: cómo ver qué pasa: `GET /api/ids/status` (estado de cada paso y del último ciclo) y `GET /api/ids/logs` (eventos recientes, errores con su detalle y consumo de la API), los dos con el token del ID Manager; también por la consola del servidor.
- MP-77: reglas de operación: después de un cambio de código o de configuración hay que reiniciar el servicio; nunca correr una pasada manual con el servicio encendido; mudarlo de máquina exige llevar la base con respaldo y apagar antes el anterior.

## Si el servicio está apagado

- MP-78: sigue funcionando: las vistas, lo que cada persona escribe, las fórmulas, los colores y las automatizaciones de Smartsheet.
- MP-79: se atrasa hasta que vuelva: los IDs (quedan `Pending ID`), los trámites quedan sueltos sin ir bajo su proyecto, no aparecen filas nuevas en las hojas de equipo (y por eso no salen sus avisos de asignación), los estados no vuelven a la maestra, `Obs` no se actualiza y el metraje corregido no pasa. Al volver se pone al día solo, por tandas; no se pierde nada.

## El flujo de un proyecto, paso a paso

- MP-80: crear el proyecto. Persona (coordinadora), vista `PROJECTS`: `Type of Project` (`KMV-P` diseño o `KMV-Miscellaneous` permisos), `Customer`, `Date Received`, `Project Name`; asigna `Designers` y `Permitting Team`. Smartsheet pone ingeniero y topógrafo por defecto.
- MP-81: numerar. Servicio, en menos de un minuto: el proyecto recibe su ID.
- MP-82: avisar a diseño. Smartsheet (automatización): llega a los diseñadores un correo con el enlace a la vista `DESIGN` (si se asignaron antes del ID, el aviso sale cuando llega el ID).
- MP-83: diseñar y QC. Personas (diseño), vista `DESIGN`. Al pasar a `2. Design Needs QC`, Smartsheet anota `QC IN` y avisa al ingeniero; si pasa más de 1 día sin `QC OUT`, vuelve a avisarle.
- MP-84: crear los trámites. Persona (coordinadora), vista `PERMITS`: `Type of Project` (`KMV-Permit`, `KMV-Line` o `KMV-MOT`), `Parent Project` y `Agency`; si hace falta, `Records Needed` o `Records Owner`, y `Prepare Packages` para un paquete propio. Un trámite que no requiere permiso nace en `NO PERMIT REQUIRED` y no pasa a ningún equipo.
- MP-85: ordenar y repartir. Servicio: pone el trámite bajo su proyecto, le da el ID, completa lo vacío y crea su fila en la hoja del equipo (`Permits` para permisos, líneas y proyectos de permisos; `MOT & Packages` para MOT y paquetes; Records si se pidió; `Billing` para toda fila con ID; `Design Tickets` si hay `DT Owner`).
- MP-86: avisar a cada equipo. Smartsheet (automatizaciones de cada hoja): la persona asignada recibe el aviso con el enlace a su vista; en MOT y paquetes, el aviso va a la persona de MOT y paquetes cuando la coordinadora asigna el trabajo.
- MP-87: trabajar el trámite. Personas (cada equipo), en su vista: estados, fechas, números. Smartsheet calcula los días y muestra sólo la revisión que toca; anota fechas como `LT Records`.
- MP-88: resultados a la maestra. Servicio: el estado y los datos del equipo vuelven a la fila del trámite y del proyecto (MP-68); `Records Status` lo calcula la maestra leyendo la hoja de Records.
- MP-89: metraje y facturación. Personas: diseño carga el metraje en la maestra; facturación lo ve en `Billing` y lleva las facturas. Si facturación corrige el metraje, el servicio lo lleva a la maestra y avisa (MP-70). Smartsheet avisa al ingeniero cuando una factura queda lista y, los lunes, las enviadas sin cobrar.
- MP-90: notas. Personas: siempre como comentario de la fila; el servicio las copia a `Obs`.
- MP-91: el cliente. Smartsheet: cada cliente ve sus proyectos en la vista `CUSTOMERS`; en producción recibe un correo cuando su estado cambia.
- MP-92: cancelar o cerrar. Persona: `CANCELLED` en la fila (nunca se borra) o el estado de cierre; `Closed` lo calcula la maestra y el servicio deja de repartir lo cerrado.
