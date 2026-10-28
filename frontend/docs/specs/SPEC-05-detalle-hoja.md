# SPEC-05 Detalle de una hoja: cabecera y pestañas

Estado: aprobada (cabecera en F1; Auditoría, Actividad y Automatizaciones en F3)
Responsable del código: `features/sheets/SheetHeader.tsx`, `features/sheets/SheetTabs.tsx`, `features/audit/`, `features/activity/`, `features/automations/`
Relacionadas: backend SPEC-B05, SPEC-B08, SPEC-B10; ADR-11; UX-01, UX-20, UX-24, UX-31, UX-34

## Objetivo

Todo lo que el panel sabe de una hoja en un solo lugar, sin que lo lento retrase ver quién tiene acceso.

## Cabecera

1. `GET /api/sheets/{id}`: nombre, insignias de SPEC-02, "Abrir en Smartsheet" (`permalink`, pestaña nueva; las hojas de otra persona no tienen enlace), "Actualizado hace X" con "Actualizar".
2. `/hojas/:sheetId` acepta id o código de permalink; si llega un código, la URL se reemplaza por el id (`history.replace`).

## Pestañas (`?tab=`)

Permisos (por defecto, SPEC-03), Auditoría, Actividad, Automatizaciones, Calidad de datos (SPEC-09). Cada pestaña pide sus datos sólo al abrirse (ADR-11).

### Auditoría (`GET /api/sheets/{id}/audit`)

1. Fila de StatTiles: total de accesos, externos (o "No se pudo saber" si `org_known: false`), sin nombre, fuera de contactos.
2. Alertas por severidad (alta, media, informativa) con icono y texto (`lib/severity.ts`): código traducido, mensaje, cantidad y lista de personas afectadas con su nivel. Cada persona enlaza a su detalle (SPEC-04).
3. "Por nivel" y "Por origen" con MeterBar; "Por dominio" en lista con insignia "Personal" en dominios personales.
4. Sin alertas: EmptyState "Sin alertas en esta hoja".

### Actividad (`GET /api/sheets/{id}/activity?days=`)

1. Selector de período: 7, 30 (por defecto), 90 y 365 días.
2. StatTiles: filas totales, modificadas en el período, editores activos, con edición sin cambios.
3. `limitations` siempre visible como StatusAlert informativo; si el primero es el aviso de cuenta dominante, StatusAlert de advertencia (UX-31).
4. Tabla de filas modificadas (`changed_rows`, hasta `limit`): número, etiqueta, último editor, cuándo. Clic en una fila abre `RowHistoryDialog` con `GET /api/sheets/{id}/rows/{rowId}/history` (LoadingNotice: puede tardar 10 s).
5. Editores: nombre o correo, filas, último cambio y nivel actual (o "Ya no tiene la hoja compartida").
6. "Con edición sin cambios en el período" (`idle_editors`) con su nivel, y la advertencia si el aviso de cuenta dominante está presente.

### Automatizaciones (`GET /api/sheets/{id}/automations`)

1. StatTiles por estado: funcionan, con problemas, apagadas.
2. Una tarjeta por regla: nombre, estado (insignia con icono), tipo y frecuencia, a quién avisa (correos y columnas con su tipo; columna no de contacto marcada), motivo de Smartsheet y problemas en lenguaje del usuario.
3. Texto fijo: "Para corregirlas, ábralas en Smartsheet: Automatización > Administrar flujos de trabajo." (el panel no las cambia).

## Estados (por pestaña)

- Carga: esqueleto con la forma de la pestaña.
- Vacío: texto propio de cada pestaña.
- Éxito: contenido.
- Parcial: Actividad con `limitations`; Auditoría con `org_known: false`.
- Error: StatusAlert dentro de la pestaña; las demás pestañas siguen funcionando.

## Criterios de aceptación

- CA-01: entrar a una hoja sólo pide `sheet` y `shares`; abrir Actividad pide `activity` una vez y volver no la repite mientras está fresca. Prueba: componente con MSW contando solicitudes.
- CA-02: `?tab=actividad` abre esa pestaña al cargar la URL. Prueba: e2e.
- CA-03: el aviso de cuenta dominante se muestra como advertencia y acompaña a la lista de editores sin cambios. Prueba: componente.
- CA-04: una columna destinataria que no es de contacto aparece marcada con su título. Prueba: componente.
- CA-05: un código de permalink en la URL se reemplaza por el id. Prueba: componente con MSW.

## Accesibilidad

Tabs con `role="tablist"`, flechas para moverse, `aria-controls`; StatTiles con la cifra y su etiqueta en el mismo texto accesible.
