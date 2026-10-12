# SPEC-B03 Directorio, contactos, grupos y vista por persona

Estado: implementada
Código: `api/routes/people.py`, `services/people.py`, `services/directory.py`
Relacionadas: SPEC-B01, SPEC-B02, SPEC-B04, ADR-B06, ADR-B09, ADR-B10

## Objetivo

Responder "¿a qué hojas tiene acceso esta persona?" sin abrir cada hoja, y ofrecer personas y grupos conocidos para autocompletar al dar acceso.

## Fuente en Smartsheet

- Permisos de cada hoja: los mismos de SPEC-B02, leídos para todas las hojas (ADR-B09).
- Contactos: `GET /2.0/contacts` (verificado: 44; sólo `id`, `name`, `email`; la API sólo permite leerlos).
- Usuarios de la organización: `GET /2.0/users` (verificado: 4; requiere administrador del sistema; si Smartsheet lo niega, se omite).
- Grupos: `GET /2.0/groups` (verificado: 2).

## Comportamiento

1. `GET /api/users` arma el directorio (ADR-B10): cada contacto, cada usuario de la organización y cada persona o grupo con algún permiso, una sola vez.
2. Clave (`key`): correo en minúsculas para usuarios; `group-<id>` para grupos; `user-<id>` si un permiso de usuario no trae correo.
3. Cada `Person`: `key`, `type`, `name`, `email`, `sheet_count` (hojas distintas; 0 si no tiene acceso), `highest_level`, `is_contact`, `is_org_member`, `is_token_owner`.
4. Orden: `sheet_count` descendente, luego nombre o correo.
5. `q` filtra por nombre o correo sin tildes ni mayúsculas; `only` aplica un filtro rápido: `contacts`, `org`, `external`, `groups`, `with_access`, `without_access`.
6. `GET /api/users/{key}` devuelve `PersonDetail`: la persona y sus hojas (`PersonSheetAccess`) por nombre de hoja; propio y heredado de la misma hoja aparecen por separado.
7. Si alguna hoja falla al leer sus permisos: `incomplete: true` y `failed_sheets`; el resto se devuelve igual (Bulkhead).
8. `GET /api/contacts` y `GET /api/groups` devuelven la libreta y los grupos tal cual, con caché.
9. `refresh=true` vuelve a leer todo de Smartsheet.

## Criterios de aceptación

- CA-01: una persona con permisos en 2 hojas y en contactos aparece una vez con `sheet_count=2`, su nivel más alto y `is_contact`. Prueba: `test_people.py::test_aggregates_person_across_sheets_and_contacts`.
- CA-02: un contacto sin permisos aparece con `sheet_count=0`; `only=without_access` y `q` filtran. Prueba: `test_people.py::test_filters_and_search`.
- CA-03: una hoja que falla no impide el resultado y queda en `failed_sheets`. Prueba: `test_people.py::test_failed_sheet_marks_incomplete`.
- CA-04: el detalle lista hojas propias y heredadas. Prueba: `test_people.py::test_person_detail_lists_sheets`.
- CA-05: clave desconocida responde 404 `PERSON_NOT_FOUND`. Prueba: `test_people.py::test_unknown_person_is_404`.
- CA-06: lectura real: 49 entradas (36 con acceso, 13 sin acceso), primera carga 3,3 s, desde caché 19 ms. Prueba: manual, 2026-10-12 (RESULTADOS).

## Pendientes

- Quitar a una persona de todas sus hojas desde esta vista (PEN-11).
- Exportar la matriz a CSV (PEN-12).
