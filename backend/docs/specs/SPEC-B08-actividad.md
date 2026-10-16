# SPEC-B08 Actividad de una hoja

Estado: implementada
Código: `api/routes/activity.py`, `services/activity.py`, `services/activity_rules.py`, `services/smartsheet/client.py`
Relacionadas: SPEC-B02, SPEC-B05, B-08, PEN-21

## Objetivo

Ver quién modificó qué en una hoja y cuándo, con datos directos de Smartsheet, y cruzarlo con los permisos: quién edita de verdad y quién tiene edición sin usarla.

## Fuentes verificadas (2026-10-16, plan 2026 de Crown Castle)

- No existe endpoint del "Registro de actividad" de la web: `/sheets/{id}/activity`, `/activityLog` y `/events` responden 404; `/events` (Event Reporting) responde 403 `errorCode` 1013 por el plan (B-08).
- Columnas: `GET /2.0/sheets/{id}/columns?includeAll=true` (117 columnas; una `primary`).
- Filas con autoría: `GET /2.0/sheets/{id}?include=writerInfo&columnIds={primaria}&pageSize=500&page=N`: cada fila con `rowNumber`, `createdAt`, `createdBy`, `modifiedAt`, `modifiedBy` (`name`, `email`) y la celda primaria como etiqueta. 2050 filas en el plan 2026.
- Historial de una celda: `GET /2.0/sheets/{id}/rows/{rowId}/columns/{columnId}/history?includeAll=true`: `value`, `displayValue`, `modifiedAt`, `modifiedBy`.

## Comportamiento

### Actividad de la hoja

1. `GET /api/sheets/{sheet_id}/activity?days=30&limit=100&refresh=` (id o código de permalink).
2. Lee todas las filas con su autoría (caché `rows:{sheet_id}`).
3. `changed_rows`: filas cuya última modificación cae en los últimos `days` días (1 a 3650), de la más reciente a la más antigua, hasta `limit` (1 a 1000): fila, número, etiqueta (celda primaria), quién la creó y cuándo, quién la modificó por última vez y cuándo.
4. `editors`: por persona que aparece como último modificador en el período: cantidad de filas, última modificación y su nivel actual en la hoja (o `null` si ya no tiene acceso).
5. `idle_editors`: personas con `EDITOR` o superior en la hoja (sin el propietario) que no son último modificador de ninguna fila en el período.
6. Si una cuenta es la última en modificar más del 80 % de las filas del período, `limitations` empieza con un aviso: probable automatización o carga masiva que tapa a los demás editores; `idle_editors` deja de ser fiable (verificado: en el plan 2026 una cuenta tocó el 92 %).
7. `limitations`: siempre informa que sólo se ve la última modificación de cada fila (un cambio sobrescrito por otro no aparece) y que borrados y cambios de permisos no se ven sin Event Reporting.

### Historial de una fila

1. `GET /api/sheets/{sheet_id}/rows/{row_id}/history?column_id=`.
2. Con `column_id`: historial de esa celda. Sin `column_id`: de las columnas con valor en la fila (`GET /2.0/sheets/{id}/rows/{rowId}`), con la concurrencia del cliente; una columna que falla se omite y se cuenta en `failed_columns`. No se piden las 117 columnas: costaría 117 solicitudes por fila de un límite de 300 por minuto; una celda vaciada sólo se ve pidiendo su `column_id`.
3. Cada cambio: columna (id y título), valor mostrado, quién y cuándo; orden del más reciente al más antiguo.
4. Sin columnas con historial: lista vacía.

## Criterios de aceptación

- CA-01: `changed_rows` filtra por días y ordena por fecha. Prueba: `test_activity.py::test_changed_rows_by_period`.
- CA-02: `editors` cruza con el nivel actual y marca a quien ya no tiene acceso. Prueba: `test_activity.py::test_editors_with_current_level`.
- CA-03: `idle_editors` lista editores sin cambios en el período, sin el propietario. Prueba: `test_activity_rules.py::test_idle_editors`.
- CA-08: aviso de cuenta dominante por encima del 80 %. Prueba: `test_activity_rules.py::test_dominance_warning_when_one_account_hides_the_rest`.
- CA-04: historial de una fila une todas las columnas ordenado y tolera una columna fallida. Prueba: `test_activity.py::test_row_history_all_columns`.
- CA-05: lectura paginada de filas (`page`). Prueba: `test_activity.py::test_rows_are_paginated`.
- CA-06: sólo lectura: ninguna escritura a Smartsheet. Prueba: las anteriores verifican `writes(...) == []`.
- CA-07: lectura real del plan 2026. Prueba: manual (RESULTADOS).
