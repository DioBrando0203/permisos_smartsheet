# SPEC-B07 Revisión de riesgos de toda la cuenta

Estado: implementada
Código: `api/routes/reports.py` (`account_review`), `services/account_review.py`
Relacionadas: SPEC-B05, ADR-B12, PEN-18

## Objetivo

Responder de una vez "¿dónde están los accesos riesgosos en toda la cuenta y quiénes son?", sin abrir hoja por hoja. Es la base de las alertas automáticas (PEN-18): la tarea programada sólo tendrá que llamar a esta revisión y comparar con la anterior.

## Comportamiento

1. `GET /api/review?q=&min_severity=&refresh=` aplica las reglas de `audit_rules.RULES` (las mismas de SPEC-B05) a cada hoja filtrada por `q`.
2. `min_severity`: `high`, `medium` o `info` (por defecto `medium`); sólo se cuentan alertas de esa severidad o mayor.
3. Respuesta `AccountReview`:
   - `totals`: hojas revisadas, hojas con alertas y personas afectadas por código.
   - `sheets`: por hoja con alertas: id, nombre, `has_dynamic_view` y conteo por código; orden por severidad máxima y luego por cantidad.
   - `people`: por persona afectada en alguna hoja: clave, nombre, correo, códigos y `sheet_count` de hojas donde tiene alertas; orden por cantidad de hojas. Una persona externa que puede compartir 26 hojas aparece primero.
   - `failed_sheets`: hojas que no se pudieron leer (Bulkhead).
4. Sólo lectura: ninguna llamada de escritura a Smartsheet.

## Criterios de aceptación

- CA-01: agrega por hoja y por persona con las mismas reglas de la auditoría. Prueba: `test_review.py::test_review_aggregates_sheets_and_people`.
- CA-02: `min_severity=high` deja sólo `EXTERNAL_CAN_SHARE`. Prueba: `test_review.py::test_min_severity_filters`.
- CA-03: una hoja que falla queda en `failed_sheets` y el resto se revisa. Prueba: `test_review.py::test_failed_sheet_is_reported`.
- CA-04: revisión real de las 100 hojas: tiempo y conteos en RESULTADOS. Prueba: manual.
