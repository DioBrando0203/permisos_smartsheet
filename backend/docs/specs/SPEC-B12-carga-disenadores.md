# SPEC-B12 Carga y acceso de los diseñadores

Estado: implementada
Código: `api/routes/designers.py`, `services/designers.py`, `services/workload_rules.py`
Relacionadas: SPEC-B03, SPEC-B09, SPEC-B11, ADR-B15, PEN-26

## Objetivo

Ver en una sola respuesta cuánto trabajo abierto tiene cada diseñador en todas las hojas, en qué fase, y si tiene acceso a las hojas donde está asignado. Tipo (ADR-B15): Smartsheet no tiene una vista de carga entre hojas sin armar informes a mano, y no cruza asignaciones con permisos. Sólo lectura; es la base para asignar mejor (PEN-26).

## Fuentes verificadas (2026-10-16)

- Asignación: `Designer1` y `Designer2` (`PICKLIST` con nombres; 19 y 29 opciones en el plan 2026).
- Estado: `Project Status` (`PICKLIST`, 69 opciones): fases numeradas `1.` a `9.` (Survey, Design, Packages/APP, Permit, Design MOT, Permit MOT, As-Built, Close, extensiones), separadores `-----` y estados generales (`CANCELLED`, `COMPLETE`, `IN PERMITTING`, `IN PROGRESS`, `NO PERMIT REQUIRED`).
- Catálogo "Source Designers": sólo nombres, sin correos (SPEC-B11).

## Configuración (`backend/.env`; cada parámetro también se puede pasar en la consulta)

- `APP_DESIGNER_COLUMNS` (por defecto `Designer1,Designer2`).
- `APP_STATUS_COLUMN` (por defecto `Project Status`).
- `APP_CLOSED_STATUSES`: estados que no cuentan como trabajo abierto. Por defecto `CANCELLED,COMPLETE,8. Process completed,4. Permit Cancelled,4. Permit Closed,4. No Permit Required,NO PERMIT REQUIRED`. Es una regla de negocio: la confirma o ajusta el usuario.
- `APP_DESIGNER_CATALOG_SHEET` y `APP_DESIGNER_CATALOG_COLUMN` (opcionales): para marcar si cada diseñador está en el catálogo.

## Comportamiento

1. `GET /api/designers?q=&designer_columns=&status_column=&closed_status=&refresh=` revisa las hojas del token (filtradas por `q`) que tienen al menos una columna de diseñador.
2. Cada fila con diseñador cuenta una asignación por diseñador distinto (una fila con el mismo nombre en `Designer1` y `Designer2` cuenta una vez).
3. Estado de la fila: `closed` si está en la lista de cerrados (sin distinguir mayúsculas ni espacios), `on_hold` si contiene "hold", si no `open`. Sin estado o con un separador `---`: `open` y se cuenta en `without_status`.
4. Fase: el número antes del primer punto (`2. Design Process` es fase `2`); sin número, `other`.
5. Por diseñador: nombre, `in_catalog` (o `null` sin catálogo), persona del directorio por nombre (sin tildes ni mayúsculas; si hay varias, `ambiguous`), `open`, `on_hold`, `closed`, `by_phase` (sólo abiertas y en espera) y por hoja: abiertas, cerradas, `has_access` (si la persona tiene la hoja compartida; `null` si no se pudo identificar) y su nivel.
6. `sheets_without_access`: hojas con trabajo abierto del diseñador a las que no tiene acceso. Es la señal principal: alguien asignado que no puede ver su trabajo.
6a. Una fila con el título de una columna de diseñador como valor ("Designer1") es un encabezado copiado: no cuenta como trabajo ni como fila sin diseñador; se suma en `header_like_rows`.
7. Totales: hojas revisadas, hojas con columnas de diseñador, asignaciones abiertas y cerradas, filas abiertas sin diseñador por hoja.
8. Orden: más trabajo abierto primero. Hojas que fallan: `failed_sheets` (Bulkhead).

## Criterios de aceptación

- CA-01: estado y fase de cada fila según la lista de cerrados, "hold" y el número inicial. Prueba: `test_workload_rules.py::test_status_and_phase`.
- CA-02: un nombre en dos columnas de la misma fila cuenta una vez. Prueba: `test_workload_rules.py::test_same_designer_in_two_columns`.
- CA-03: el nombre se asocia a una persona del directorio sin tildes ni mayúsculas; con dos coincidencias queda `ambiguous`. Prueba: `test_workload_rules.py::test_match_person`.
- CA-04: `has_access` y `sheets_without_access` según los permisos de cada hoja. Prueba: `test_designers.py::test_workload_and_access`.
- CA-05: sólo lectura. Prueba: `test_designers.py` verifica `writes(...) == []`.
- CA-06: revisión real de la cuenta. Prueba: manual (RESULTADOS).
