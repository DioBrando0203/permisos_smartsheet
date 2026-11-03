# SPEC-B15 Validación de proyecto por cliente

Estado: implementada para consulta configurable (PEN-24). Sólo lectura; correspondencia de columnas del piloto pendiente de confirmar.

## Objetivo y contrato

- VB-01: `GET /api/sheets/{sheet_id}/project-associations` recibe `customer_column`, `project_column`, `catalog_sheet`, `catalog_customer_column`, `catalog_project_column` y `refresh` opcional. Los nombres o IDs de columnas y la hoja catálogo los indica quien consulta; no se suponen columnas del piloto.
- VB-02: Lee la hoja y el catálogo desde Smartsheet con el cliente y caché existentes. Devuelve hojas, columnas, número de filas revisadas, número total de problemas, hasta 200 problemas y `truncated`.
- VB-03: Ignora filas sin proyecto seleccionado. Para las demás detecta cliente vacío, proyecto inexistente, proyecto con varios clientes en el catálogo y cliente diferente. Compara sin distinguir mayúsculas ni espacios exteriores; no elimina ni modifica referencias históricas y no filtra por estado activo.
- VB-04: Un catálogo con proyecto sin cliente no permite validar ese proyecto y se informa como ambiguo. No se presupone que un proyecto aparezca una sola vez; repetición con el mismo cliente es válida.
- VB-05: Columnas desconocidas devuelven `COLUMN_NOT_FOUND`; no se escriben datos ni se accede a PostgreSQL. La revisión ocurre después de guardar y no bloquea la edición ni implementa selectores.

## Criterios de aceptación

- CA-01: Coincidencias, diferencias, vacíos y proyectos inexistentes se clasifican correctamente con normalización.
- CA-02: Proyectos con clientes contradictorios o sin cliente se reportan ambiguos; proyectos históricos siguen siendo válidos si están en catálogo.
- CA-03: El endpoint lee únicamente columnas necesarias, limita la respuesta a 200 filas manteniendo el conteo total y no escribe a Smartsheet.
- CA-04: Hoja o columna inexistente se informa mediante los errores existentes; pruebas con Smartsheet simulado.

## Verificación del piloto

- VB-06: El usuario confirmó que `Tareas.Tracking Project` refiere a `Proyectos.Tracking Project`. Una comparación de esos campos y `Customer Code` revisó 6 filas y no encontró problemas. `Linked Tracking` representa un proyecto relacionado y puede ser histórico; una comparación exploratoria anterior con ese campo encontró 2 valores ausentes del catálogo piloto, lo cual no demuestra un error.
- VB-07: Ninguna escritura; recursos modificables únicamente en workspace `Pruebas`, sujetos además a autorización expresa y modo solo lectura.
- VB-08: Según el usuario, referencias históricas ausentes del catálogo piloto no son necesariamente inválidas. `unknown_project` sólo indica ausencia en el catálogo consultado; no determina validez histórica ni autoriza cambios.
