# SPEC-09 Calidad de datos y referencias entre hojas

Estado: borrador (pestaña de hoja en F3; referencias de la cuenta en F4)
Responsable del código: `features/quality/`
Relacionadas: backend SPEC-B09, SPEC-B11; UX-12, UX-29

## Objetivo

Encontrar identificadores repetidos o mal formados, datos obligatorios vacíos y valores que no existen en una hoja catálogo, sin filtrar a mano en Smartsheet.

## Comportamiento

### Pestaña Calidad de datos de una hoja

1. `GET /api/sheets/{id}/columns` para elegir columnas (buscador por título; muestra el tipo).
2. Formulario `QualityForm`:
   - "No deben repetirse" (multiselección de columnas) → `unique`.
   - "No deben estar vacías" → `required`.
   - "Deben cumplir un formato": columna + expresión regular, con ejemplos ("sólo números: `^\d+$`") → `pattern` (`Columna=expresión`).
   - "Deben existir en otra hoja": columna, hoja catálogo (SheetPicker) y columna del catálogo → `GET /api/sheets/{id}/references`.
   - Valores iniciales sugeridos si existen en la hoja: `Record ID` (no repetir, sólo números), `Designer1` (no vacía, existir en "Source Designers").
3. "Revisar" hace la consulta (no al escribir). La revisión elegida queda en la URL para compartirla.
4. Resultados por revisión: columna, tipo, cantidad de filas con problema, y lista agrupada por valor con las filas (número y etiqueta) y "Abrir en Smartsheet". Si `truncated`, "Se muestran las primeras 200 filas de N".
5. Errores de la revisión (`COLUMN_NOT_FOUND` con sugerencias, `INVALID_PATTERN`, `NO_CHECKS`) junto al campo (UX-12).

### Referencias en toda la cuenta (sección de `/revision`)

1. Columna, hoja catálogo y columna del catálogo (por defecto `Designer1` contra "Source Designers" / `Designer`), buscador de hojas opcional.
2. `GET /api/references`: StatTiles (hojas revisadas, sin la columna, filas fuera del catálogo); "Valores que faltan en más hojas" (`by_value`: valor, hojas, filas) y tabla por hoja con enlace a su pestaña Calidad.
3. Nota: "Un valor que falta en muchas hojas suele ser un catálogo desactualizado, no un error de tipeo."

## Estados

- Carga: spinner en "Revisar"; LoadingNotice en la vista de cuenta.
- Vacío: "Sin problemas en las columnas revisadas".
- Éxito: resultados.
- Parcial: `failed_sheets` en la vista de cuenta.
- Error: junto al campo o StatusAlert.

## Criterios de aceptación

- CA-01: el formulario arma `unique`, `required` y `pattern` repetidos en la query tal como espera el backend. Prueba: unitaria.
- CA-02: `truncated` muestra el aviso con el total real (`issues_count`). Prueba: componente.
- CA-03: `COLUMN_NOT_FOUND` muestra la sugerencia del backend junto a la columna. Prueba: componente con MSW.
- CA-04: la revisión en la URL se reproduce al recargar. Prueba: e2e.
