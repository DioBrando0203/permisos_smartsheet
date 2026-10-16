# SPEC-B11 Referencias entre hojas

Estado: implementada
Código: `api/routes/quality.py` (`sheet_references`, `account_references`), `services/references.py`, `services/quality_rules.py`
Relacionadas: SPEC-B09, ADR-B15, PEN-24

## Objetivo

Comprobar que los valores de una columna existen en otra hoja que sirve de catálogo; por ejemplo, que cada diseñador asignado en los planes (`Designer1`, `Designer2`) esté en "Source Designers". Tipo (ADR-B15): Smartsheet no revisa referencias entre hojas; el panel sólo lee.

## Fuentes verificadas (2026-10-16)

- "Source Designers" (`4315680049418116`): 25 filas, columna `Designer`. Es el catálogo de diseñadores.
- No hay una hoja maestra de Record IDs entre las del token; las 4 hojas de la organización no compartidas son copias y una de prueba.

## Comportamiento

1. `GET /api/sheets/{sheet_id}/references?column=&catalog_sheet=&catalog_column=&refresh=`:
   - `column`: columna de la hoja a revisar (título o id). `catalog_sheet`: id o código del permalink. `catalog_column`: columna del catálogo.
   - Compara sin distinguir mayúsculas ni espacios a los lados. Celdas vacías no cuentan (para eso está `required` de SPEC-B09).
   - Respuesta `SheetReferences`: `column`, `catalog` (hoja y columna), `catalog_values_count`, `checked_rows`, `missing_count` y hasta 200 `missing` agrupados por valor con sus filas.
2. `GET /api/references?column=&catalog_sheet=&catalog_column=&q=&refresh=`: la misma revisión en todas las hojas del token que tienen esa columna (filtradas por `q`), sin el catálogo. Por hoja: `missing_count` y valores faltantes; totales por valor (qué valor falta en más hojas). Hojas sin la columna se cuentan en `sheets_without_column`; las que fallan, en `failed_sheets`.
3. Columna desconocida en la hoja o en el catálogo: 404 `COLUMN_NOT_FOUND` (en la vista de cuenta, la hoja se omite sin error).
4. Sólo lectura; columnas y filas con la misma caché de SPEC-B09.

## Criterios de aceptación

- CA-01: valores que no están en el catálogo, sin distinguir mayúsculas ni espacios, ignorando vacíos. Prueba: `test_quality_rules.py::test_missing_references`.
- CA-02: vista por hoja con catálogo por código de permalink. Prueba: `test_references.py::test_sheet_references`.
- CA-03: vista de cuenta: omite el catálogo, cuenta hojas sin la columna y suma faltantes por valor. Prueba: `test_references.py::test_account_references`.
- CA-04: sólo lectura. Prueba: las anteriores verifican `writes(...) == []`.
- CA-05: revisión real de `Designer1` contra "Source Designers". Prueba: manual (RESULTADOS).
