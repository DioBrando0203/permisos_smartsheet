# SPEC-B09 Calidad de datos de una hoja

Estado: implementada
Código: `api/routes/quality.py`, `services/quality.py`, `services/quality_rules.py`
Relacionadas: SPEC-B08, ADR-B15, PEN-24

## Objetivo

Encontrar en segundos lo que en Smartsheet exige filtrar a mano: identificadores repetidos o mal formados y filas sin un dato obligatorio (por ejemplo, sin diseñador). Tipo (ADR-B15): Smartsheet no lo tiene como revisión de una sola vez; no cambia nada en la hoja ni en cómo trabaja la gente.

## Fuentes verificadas (2026-10-16, plan 2026 de Crown Castle)

- `GET /2.0/sheets/{id}/columns`: 117 columnas; entre ellas `Record ID`, `Design Ticket`, `Permit #` (texto), `Designer1`, `Project Status` (lista).
- `GET /2.0/sheets/{id}?columnIds=…&pageSize=500&page=N`: celdas sólo de las columnas pedidas.

## Comportamiento

1. `GET /api/sheets/{sheet_id}/columns`: columnas con id, título, tipo, índice y si es primaria (para saber qué revisar).
2. `GET /api/sheets/{sheet_id}/quality?unique=&required=&pattern=&refresh=`:
   - `unique` (repetible): columnas cuyos valores no deben repetirse. Revisa valores sin espacios a los lados y sin distinguir mayúsculas; las celdas vacías no cuentan.
   - `required` (repetible): columnas que no deben quedar vacías.
   - `pattern` (repetible): `Columna=expresión regular` que debe cumplir cada valor no vacío (por ejemplo `Record ID=^\d{5}$`). Expresión de hasta 100 caracteres; valores de hasta 500.
   - Columnas por título (sin distinguir mayúsculas) o por id. Una desconocida: 404 `COLUMN_NOT_FOUND` con los títulos parecidos.
   - Al menos una revisión; si no, 422 `NO_CHECKS`. Máximo 20 columnas en total.
3. Lee sólo las columnas pedidas (más la primaria como etiqueta), con caché por hoja y columnas.
4. Respuesta `SheetQuality`: `rows_total` y por revisión `column`, `check` (`unique`, `required`, `pattern`), `issues_count` y hasta 200 `issues`: valor (para `unique` y `pattern`), filas (`row_id`, `row_number`, `label`).
5. Sólo lectura.

## Criterios de aceptación

- CA-01: `unique` agrupa repetidos sin distinguir mayúsculas ni espacios e ignora vacíos. Prueba: `test_quality_rules.py::test_duplicates`.
- CA-02: `required` lista filas vacías. Prueba: `test_quality_rules.py::test_missing`.
- CA-03: `pattern` lista valores que no cumplen; expresión inválida: 422 `INVALID_PATTERN`. Prueba: `test_quality.py::test_pattern_and_invalid_regex`.
- CA-04: columna desconocida: 404 `COLUMN_NOT_FOUND`; sin revisiones: 422 `NO_CHECKS`. Prueba: `test_quality.py::test_errors`.
- CA-05: sólo pide las columnas necesarias y no escribe. Prueba: `test_quality.py::test_reads_only_needed_columns`.
- CA-06: revisión real del plan 2026. Prueba: manual (RESULTADOS).
