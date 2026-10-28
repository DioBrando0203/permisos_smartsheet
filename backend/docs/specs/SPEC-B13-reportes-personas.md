# SPEC-B13 Reportes asociados a personas y contactos

Estado: aprobada (2026-10-28, solicitada por el usuario)
Código: `api/routes/people.py`, `services/person_reports.py`, `services/smartsheet/`

## Objetivo

Mostrar en el detalle de una persona o contacto todos los reportes que Smartsheet permite relacionar sin suponer acceso.

## Fuente y relaciones

- `GET /2.0/reports`: lista todo reporte accesible; conserva id, nombre, nivel del token y si es reporte de resumen.
- `GET /2.0/reports/{id}?include=sourceSheets`: identifica sus hojas fuente.
- `GET /2.0/shares?assetType=report&assetId={id}`: identifica permisos directos del reporte.
- Directo: la persona o grupo figura en los permisos del reporte.
- Por hoja fuente: tiene acceso a al menos una hoja fuente; no afirma que pueda abrir el reporte.
- Sin relación: no se devuelve. Un reporte cuya API no permite leer permisos se devuelve con la limitación, no se deduce acceso.

## Contrato

- `GET /api/users/{key}/reports?refresh=` devuelve persona, reportes y fallos parciales.
- Cada reporte: id, nombre, tipo (`row` o `summary`), nivel del token, relaciones directas y hojas fuente coincidentes; `direct_access_known` y `limitations` hacen explícito lo desconocido.

## Criterios de aceptación

- CA-01: un reporte de filas y uno de resumen se clasifican correctamente.
- CA-02: el permiso directo se diferencia de una hoja fuente coincidente.
- CA-03: una falla al leer un reporte no borra los demás y se informa.
- CA-04: las pruebas sólo usan respuestas simuladas de Smartsheet.
