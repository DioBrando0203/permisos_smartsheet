# SPEC-08 Carga y acceso de los diseñadores

Estado: borrador (fase F4)
Responsable del código: `features/designers/`
Relacionadas: backend SPEC-B12, PEN-26, PEN-27; ADR-09; UX-29, UX-34

## Objetivo

Ver cuánto trabajo abierto tiene cada diseñador, en qué fase, y quién está asignado en hojas que no puede abrir.

## Comportamiento

1. `/disenadores` pide `GET /api/designers` (unos 14 s la primera vez: LoadingNotice, UX-29).
2. StatTiles: hojas con diseñadores, asignaciones abiertas, en espera, cerradas, diseñadores con hojas sin acceso.
3. StatusAlert informativo con la regla usada: "Cuentan como cerrados: {closed_statuses}" y enlace "Cambiar" que abre un selector de estados (multiselección); la elección viaja como `closed_status` en la URL y no se guarda en el servidor (PEN-27 la fija en `.env`).
4. Tabla de diseñadores (orden del backend: más abiertas primero): nombre, abiertas, en espera, cerradas, MeterBar de abiertas por fase (`by_phase`, fases 1 a 9 y "otra", con los números visibles), "Hojas sin acceso" (insignia de advertencia si es mayor que 0), "No está en el catálogo" (si `in_catalog` es `false`) y "Sin cuenta identificada" (si `person` es `null`; "Nombre ambiguo" si `ambiguous`).
5. Expandir un diseñador muestra sus hojas: abiertas, en espera, cerradas, acceso ("Tiene acceso: Editor" / "Sin acceso" en advertencia / "No se pudo saber") con enlace a la hoja.
6. "Filas abiertas sin diseñador" (`sheet_gaps`): tabla por hoja con enlace.
7. `header_like_rows` mayor que 0: nota "Se ignoraron N filas que repiten los encabezados de las columnas de diseñador."

## Estados

- Carga: esqueleto y LoadingNotice.
- Vacío: "No hay hojas con columnas de diseñador".
- Éxito: tablas.
- Parcial: `failed_sheets` con StatusAlert de advertencia.
- Error: StatusAlert con texto por código y "Reintentar".

## Criterios de aceptación

- CA-01: la MeterBar de fases muestra los mismos números que `by_phase` y la suma coincide con abiertas más en espera. Prueba: componente.
- CA-02: cambiar los estados cerrados vuelve a pedir con `closed_status` y la URL lo conserva. Prueba: componente con MSW.
- CA-03: un diseñador con `has_access: false` en una hoja con trabajo abierto muestra "Sin acceso" en advertencia y cuenta en el StatTile. Prueba: componente.
- CA-04: "No se pudo saber" cuando `has_access` es `null` (no se muestra como "Sin acceso"). Prueba: componente.

## Pendientes

- Asignar desde el panel viendo la carga (PEN-26): exige OAuth y escrituras.
