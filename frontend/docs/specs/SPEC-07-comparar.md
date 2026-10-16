# SPEC-07 Comparar hojas y copiar permisos

Estado: borrador (comparar y simular en F4; ejecutar en F5)
Responsable del código: `features/compare/`
Relacionadas: backend SPEC-B05 (comparación), SPEC-B06 (copia); ADR-B13 del backend; UX-28, UX-30

## Objetivo

Ver qué cambió en el equipo entre dos hojas (por ejemplo, el plan de un año y el del siguiente) y preparar la nueva hoja con el mismo equipo sin hacerlo persona por persona.

## Comportamiento

1. `/comparar?a=&b=` con dos `SheetPicker` (buscador sobre la lista de hojas de SPEC-02; acepta pegar una URL de Smartsheet y extrae el código del permalink).
2. Con las dos elegidas, `GET /api/sheets/compare?a=&b=`:
   - StatTiles: sólo en A, sólo en B, con distinto nivel, iguales.
   - Tres listas: sólo en A, sólo en B, distinto nivel (nivel en A y en B).
   - "Intercambiar A y B".
3. "Copiar los permisos de A a B":
   - Opciones: "Subir el nivel de quien ya está con menos" (`upgrade_levels`), "Incluir los heredados del workspace de A" (`include_inherited`).
   - "Ver qué pasaría": `POST /api/sheets/{B}/shares/copy` con `dry_run: true`. Tabla de pasos con acción traducida (Agregar, Subir nivel, Sin cambios, Omitir), persona, nivel actual y nuevo, y motivo de omisión (propietario, heredado, ya tiene igual o más). Conteos por acción arriba (UX-30).
   - "Aplicar N cambios" (`primary`): `dry_run: false` tras confirmación que repite los conteos. Resultado por paso (hecho o falló). Deshabilitado en modo solo lectura (UX-28).
4. Texto fijo: "Copiar nunca baja de nivel ni quita a nadie en la hoja B; el Propietario se copia como Administrador."

## Estados

- Carga: esqueleto en las listas; la simulación con spinner en su botón.
- Vacío: "Elija dos hojas para comparar"; "Las dos hojas tienen el mismo equipo".
- Éxito: comparación y plan.
- Parcial: pasos que fallaron al ejecutar, con su motivo.
- Error: `SAME_SHEET` junto a los selectores; otros con StatusAlert.

## Criterios de aceptación

- CA-01: pegar `https://app.smartsheet.com/sheets/<código>?view=grid` elige la hoja correcta. Prueba: unitaria del extractor de código.
- CA-02: la URL con `a` y `b` reproduce la comparación al recargar. Prueba: e2e.
- CA-03: la simulación funciona con `read_only: true` y el botón de aplicar queda deshabilitado con el motivo. Prueba: componente con MSW.
- CA-04: aplicar envía `dry_run: false` sólo tras confirmar y luego invalida la hoja destino. Prueba: componente con MSW (F5).
