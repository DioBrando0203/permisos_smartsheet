# SPEC-B16 Catálogo de proyectos y selector de Linked Tracking

Estado: en operación en Pruebas (2026-11-04): catálogo sincronizado y Linked Tracking vinculado por el usuario; flujo completo comprobado por API. Resaltado en rojo creado y comprobado por el usuario (LB-16). Falta que confirme en la interfaz el filtrado al escribir el código del cliente (PEN-24).

## Capacidades nativas verificadas (documentación oficial, 2026-11-04)

- LD-01: Smartsheet tiene columnas desplegables vinculadas: las opciones de una columna Dropdown se toman de una columna de otra hoja y se actualizan casi en tiempo real. Planes de pago; Admin en la hoja destino y al menos Viewer en la origen. Fuente: help.smartsheet.com/articles/2483624 y 2483625.
- LD-02: La fuente debe ser otra hoja (no un reporte ni la misma hoja); hasta 20 000 valores; el orden es el de la hoja fuente; duplicados y vacíos se omiten.
- LD-03: "Filter dropdown options" es un filtro estático con una sola condición por columna (columna, operador, valor). No puede depender del Customer de la fila que se edita.
- LD-04: Funcionan en tabla, formularios, reportes y Dynamic View, pero sólo se configuran desde la vista de tabla. La documentación no menciona configurarlas por API.
- LD-05: "Limit to list values only" se activa al vincular y puede desactivarse para conservar valores locales (históricos).
- LD-06: Los desplegables dependientes (un desplegable filtra a otro, por fila) figuran como "In Planning" en la página de producto de noviembre de 2025; no están disponibles según lo verificado.
- LD-07: Formularios: la lógica condicional muestra u oculta campos, pero no cambia las opciones de un campo; cada campo corresponde a una columna. Dynamic View: su lógica sólo afecta al panel de detalle y se basa en valores ya guardados.
- LD-08: La API no permite opciones distintas por fila; una columna PICKLIST tiene una sola lista para toda la hoja.

## Limitación y decisión

- LD-09: Que la misma celda Linked Tracking muestre sólo proyectos del Customer de su fila no es posible hoy en tabla, formulario ni Dynamic View. Una API externa no puede cambiar el desplegable por fila.
- LD-10: Alternativa estricta descartada por ahora: una columna o campo de formulario por cliente con filtro estático, más consolidación en Linked Tracking. Con 11 clientes en `Customer` exige 11 columnas auxiliares y escritura de consolidación.
- LD-11: Recomendación: hoja catálogo en Pruebas, Linked Tracking como desplegable vinculado a ella (agrupado por cliente, búsqueda por código), validación inmediata con la fórmula existente `Control Linked Tracking` y revisión con el backend. Cuando Smartsheet publique desplegables dependientes se configura sin código.

## Contrato

- LB-01: `GET /api/catalogs/projects?customer_code=&company=&include_historical=&refresh=`: proyectos actuales (con Stable ID permanente) e históricos conocidos, ordenados por cliente, empresa e ID, y `duplicates`. Sólo lectura.
- LB-02: Históricos conocidos: opciones curadas del desplegable Linked Tracking y filas de la hoja catálogo con `Origin` = `Histórico`. Un texto sin formato de proyecto no entra al catálogo.
- LB-03: `GET /api/catalogs/linked-tracking?only_issues=`: por fila `empty`, `current_valid`, `historical_valid`, `unverifiable` (mismo cliente sin origen comprobable, o fila sin cliente), `other_customer` (incluye Customer cambiado después de asociar), `same_project` o `invalid`; además `same_company`. No modifica asociaciones.
- LB-04: `GET /api/catalogs/projects/sync-plan`: plan sin escrituras con `plan_catalog`: `add`, `update` (cambió el cliente), `unchanged`, `conflict`. Nunca propone borrados.
- LB-05: `POST /api/catalogs/projects/sync` (token `IDS_ADMIN_TOKEN`): aplica el plan en `APP_PROJECT_CATALOG_SHEET`. Exige las barreras de escritura del ID Manager, hoja distinta de las cuatro del piloto y workspace Pruebas comprobado en el momento. Sólo POST y PUT de filas del catálogo; nunca DELETE ni escrituras en Proyectos.
- LB-06: Con el procesador en modo asignación y la hoja configurada, la sincronización corre al final de cada ciclo; un fallo queda en `last_catalog_sync` de `/api/ids/status` y no afecta a los IDs.
- LB-07: Hoja catálogo: columnas `Tracking Project` (valor del desplegable), `Customer Code`, `Customer`, `Company` y `Origin` (`Actual` o `Histórico`). Un proyecto entra al tener Stable ID confirmado; los históricos pueden agregarse a mano.

## Criterios de aceptación

- CA-01: Filtros BS, CC, OT, cliente sin proyectos y empresa; históricos incluidos o excluidos.
- CA-02: Las siete clasificaciones, cliente cambiado y fila sin cliente.
- CA-03: Sincronización bloqueada sin token, sin barreras, sin hoja, con hoja del piloto o fuera de Pruebas; agrega y actualiza sin borrar y sin tocar Proyectos.
- CA-04: Lectura real del piloto sin escrituras; Stable IDs y PostgreSQL sin cambios.

## Puesta en marcha

- LB-08: Hoja `Catálogo de Proyectos (Piloto)`, id `8048198976491396`, en `Pruebas/Normalizacion de Datos - Piloto/01 Datos`, configurada en `APP_PROJECT_CATALOG_SHEET`. Primera sincronización: 11 filas (9 actuales y 2 históricas), Proyectos sin cambios de versión, segunda pasada sin cambios.
- LB-09: Tras agregar o actualizar, la sincronización ordena la hoja por `Customer Code`, `Company` y `Tracking Project`, porque el desplegable vinculado muestra el orden de la hoja fuente.
- LB-10: Ni la API documentada ni el conector de Smartsheet exponen el vínculo de desplegables; lo configura una persona con Admin en la vista de tabla. Después se comprobará con GET de columnas qué expone la API.
- LB-11: Vínculo comprobado (2026-11-04 17:24 -05:00): las opciones de Linked Tracking pasaron de 7 estáticas a las 11 del catálogo, en su orden; `validation` false; valores de celda 563, 627 y 715 conservados. El GET de columna sólo expone `options` y `validation`, no el vínculo: el servicio nunca escribe opciones en esa columna.
- LB-12: Prueba real de punta a punta: proyecto de prueba `PRUEBA - catálogo automático` (OT-Others) creado por API; Stable ID `KMV-OT-26-002` a los 45 s, fila del catálogo a los 51 s y opción del desplegable a los 57 s, sin intervención.
- LB-13: Prueba visual del usuario (2026-11-04 17:31 -05:00): en una fila BS el desplegable permitió elegir `KMV-CC-26-627` (CC), como predice LD-09. Se detectó en ambas capas: `Control Linked Tracking` = `ERROR: DIFFERENT CUSTOMER` y backend `other_customer`. No se corrige automáticamente.
- LB-14: El resaltado en rojo es un formato condicional que se crea en la interfaz: ni la API ni el conector de Smartsheet lo exponen. No se pinta por API porque exigiría reenviar el valor de la celda y podría pisar una edición simultánea.
- LB-15: Verificación del 2026-11-04 19:33 -05:00 desde el equipo Windows (sólo GET, procesador apagado en ese proceso): catálogo con 16 filas (14 actuales y 2 históricas, sin duplicados) y plan todo `unchanged`, así que la sincronización automática siguió al día. Linked Tracking: 2 `current_valid`, 2 `historical_valid`, 9 vacíos y la fila 4 de LB-13 aún `other_customer`.
- LB-16: Resaltado creado por el usuario en Proyectos (Piloto) el 2026-11-05 00:09 -05:00: formato condicional con condición en `Control Linked Tracking` = `ERROR: DIFFERENT CUSTOMER` y relleno rojo sólo en la celda Linked Tracking. El usuario confirmó que funciona; la fila 4 queda en rojo. Configuración sólo en la interfaz (LB-14); sin escrituras del servicio.
- LB-17 (2026-11-10 10:00 -05:00): la fuente del catálogo es Presentable; sólo entran filas madre (una vez por proyecto) y la empresa es `KMV` si no hay columna. Los históricos salen sólo de filas `Histórico` de la hoja catálogo: las opciones del desplegable vinculado son copia del catálogo y no se usan como fuente. Presentable no tiene `Control Linked Tracking`; hace falta agregarla para el resaltado rojo.
- LB-18 (2026-11-10 10:14 -05:00): Linked Tracking de Presentable no está vinculado al catálogo: tras vaciar y recargar el catálogo con 4 proyectos, sus opciones siguen siendo las 21 anteriores. La copia de la hoja dejó una lista fija; hay que vincularla en la vista de tabla.
- LB-19 (2026-11-10 10:20 -05:00): el usuario vinculó Linked Tracking de Presentable a `Catálogo de Proyectos (Piloto)` / `Tracking Project`, sin filtro y con "Limit to list values only" desactivado. Verificado por API: opciones iguales a los 4 proyectos del catálogo, `validation` false, valores de celda conservados y `Control Linked Tracking` en `LEGACY: NOT LOADED` para las 7 filas.
- LB-20 (2026-11-10 13:06 -05:00): `Customer List` (8537217871073156, `Pruebas/Producto`) es la lista de clientes para vincular el desplegable `Customer` de PROJECT KMV. Columnas: `Customer` (formato `CÓDIGO-Nombre`, requerido por la fórmula `Customer Code`), `Code` (fórmula), `Active` (filtro del desplegable), `Notes` y `Check` (código faltante o repetido). Se carga a mano; un código nuevo empieza su numeración en 001 (SPEC-ID01 ID-32). El vínculo se configura en la interfaz.
