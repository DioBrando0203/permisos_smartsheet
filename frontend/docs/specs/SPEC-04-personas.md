# SPEC-04 Vista por persona

Estado: borrador
Responsable del código: `features/people/`
Relacionadas: SPEC-B03 del backend, ADR-06, UX-19

## Objetivo

Saber a qué hojas tiene acceso una persona o grupo y corregirlo desde un solo lugar.

## Comportamiento

1. `/personas` lista personas y grupos con avatar, nombre, correo, número de hojas y nivel más alto. Orden: más hojas primero.
2. Filtros rápidos: "Todos", "De la organización", "Externos" (no miembros), "Grupos".
3. Buscador por nombre o correo (UX-21).
4. Al elegir una persona, `/personas/:key` muestra sus hojas con nivel, origen y las mismas acciones de SPEC-03 (cambiar nivel, quitar).
5. Aviso de que la primera carga lee todas las hojas y puede tardar ("Leyendo permisos de 100 hojas…" con progreso indeterminado).

## Estados

- Carga: esqueleto y el aviso de la primera carga.
- Vacío: "Nadie más tiene acceso a sus hojas".
- Éxito: lista.
- Parcial: `incomplete=true`: StatusAlert de advertencia "No se pudieron leer N hojas" con la lista y "Reintentar" (UX-19).
- Error: StatusAlert con texto por código y "Reintentar".

## Criterios de aceptación

- CA-01: quitar acceso desde la persona actualiza también la vista de esa hoja. Prueba: componente con MSW (invalidación de claves).
- CA-02: parcial muestra datos y aviso a la vez. Prueba: componente.
- CA-03: el filtro "Externos" sólo muestra `is_org_member=false`. Prueba: unitaria.

## Pendientes

- Quitar a una persona de todas sus hojas (PEN-11).
- Exportar a CSV (PEN-12).
