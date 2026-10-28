# SPEC-10 Reportes relacionados con personas

Estado: aprobada (2026-10-28, depende de SPEC-B13)
Responsable: `features/people/`

## Objetivo

Complementar el detalle de persona con sus reportes relacionados, sin presentar como acceso confirmado una relación por hoja fuente.

## Comportamiento

1. La sección "Reportes relacionados" carga al abrirse el detalle.
2. Cada reporte muestra nombre, tipo, nivel del token y sus hojas fuente coincidentes.
3. "Compartido directamente" se muestra sólo si la API confirmó un permiso directo.
4. "Relacionado por hoja fuente" aclara que no confirma acceso al reporte.
5. Fallos o limitaciones se muestran junto a los resultados.
