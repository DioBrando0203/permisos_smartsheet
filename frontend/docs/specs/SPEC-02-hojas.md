# SPEC-02 Lista de hojas

Estado: borrador
Responsable del código: `features/sheets/`
Relacionadas: SPEC-B01 del backend, UX-16, UX-17, UX-20, UX-21

## Objetivo

Encontrar una hoja en segundos entre todas las de la cuenta.

## Comportamiento

1. `/hojas` lista todas las hojas por nombre con: nombre, fecha de modificación relativa ("hace 3 días") y, si el token no puede administrarla, una insignia "Sólo lectura".
2. Buscador arriba (UX-21) que filtra en el navegador; el total se muestra ("12 de 100 hojas").
3. Al elegir una hoja se abre `/hojas/:sheetId` con SPEC-03 en el detalle; la fila queda seleccionada.
4. Botón "Actualizar" y "Actualizado hace X" (UX-20).

## Estados

- Carga: 10 filas esqueleto.
- Vacío: "No hay hojas en esta cuenta" (raro) o "Ninguna hoja coincide con 'x'" con "Borrar búsqueda".
- Éxito: lista.
- Parcial: no aplica.
- Error: StatusAlert con texto por código y "Reintentar".

## Criterios de aceptación

- CA-01: buscar "plan 2026" encuentra "Plan 2026" y "PLAN de 2026" sin tildes ni mayúsculas. Prueba: `lib/search.test.ts`.
- CA-02: la hoja seleccionada se mantiene marcada al volver desde el detalle en móvil. Prueba: e2e.
- CA-03: 100 hojas se desplazan sin bloquear la escritura en el buscador. Prueba: manual.

## Accesibilidad

Lista como `<ul>` con enlaces; el contador de resultados en `role="status"`.
