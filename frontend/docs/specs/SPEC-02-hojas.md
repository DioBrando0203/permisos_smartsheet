# SPEC-02 Lista de hojas

Estado: borrador (fase F1)
Responsable del código: `features/sheets/`
Relacionadas: backend SPEC-B01 (`GET /api/sheets`), PEN-14, ADR-12, UX-16, UX-17, UX-20, UX-21, UX-33

## Objetivo

Encontrar en segundos cualquier hoja de la organización y saber de un vistazo cuáles se pueden administrar.

## Comportamiento

1. `/hojas` pide `GET /api/sheets?scope=all` una vez (ADR-12) y muestra cada hoja con nombre, fecha de modificación relativa ("hace 3 días") e insignias:
   - "De otra persona" con su dueño (`owner_email`) si `in_my_list` es `false`: sólo consulta (UX-33).
   - "Sólo lectura" si `can_manage_shares` es `false` y la hoja es del token.
   - "Vista dinámica" si `has_dynamic_view` es `true` (UX-32).
2. Filtro de alcance: "Todas" (por defecto), "Mías", "De otras personas"; buscador (UX-21). Contador: "12 de 114 hojas".
3. Elegir una hoja abre `/hojas/:sheetId` (SPEC-05) y la fila queda seleccionada.
4. Cabecera de la lista: "Actualizado hace X" con "Actualizar" (`refresh=true`, UX-20) y "Exportar a Excel" (enlace a `GET /api/export/access.csv?scope=…&q=…` con el filtro actual; K-09).

## Estados

- Carga: 10 filas esqueleto.
- Vacío: "Ninguna hoja coincide con 'x'" con "Borrar búsqueda" (una cuenta sin hojas: "No hay hojas visibles para la cuenta del panel").
- Éxito: lista.
- Parcial: no aplica.
- Error: StatusAlert con texto por código y "Reintentar".

## Criterios de aceptación

- CA-01: buscar "plan 2026" encuentra "Plan 2026" y "PLAN de 2026"; "ñandu" encuentra "Ñandú". Prueba: `lib/search.test.ts`.
- CA-02: el filtro "De otras personas" muestra sólo `in_my_list=false` con su dueño. Prueba: componente con MSW.
- CA-03: la exportación usa el alcance y la búsqueda actuales en la URL del enlace. Prueba: componente.
- CA-04: la hoja seleccionada sigue marcada al volver del detalle en móvil. Prueba: e2e.
- CA-05: con 114 hojas, escribir en el buscador no se bloquea. Prueba: manual.

## Accesibilidad

Lista `<ul>` de enlaces; contador en `role="status"`; insignias con texto (no sólo color).
