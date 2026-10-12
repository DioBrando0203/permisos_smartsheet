# Documentación del frontend

Fuente de verdad del panel de permisos. Metodología: desarrollo guiado por especificaciones (SDD). Ningún cambio de comportamiento entra sin spec; ninguna spec queda sin pruebas que la verifiquen.

Estado: reglas, patrones y sistema visual definidos (2026-10-12); specs en borrador. La implementación empieza cuando el backend esté probado (PEN-06 en `backend/docs/REQUERIMIENTOS.md`).

## Orden de lectura para una IA o persona nueva

1. `GUIA_IA.md`: protocolo de trabajo, definición de terminado y prohibiciones. Obligatorio.
2. `ARQUITECTURA.md`: módulos, dependencias permitidas, flujo de datos y estado.
3. La spec del área afectada en `specs/`.
4. Las reglas: `reglas_programacion/` (P-xx), `reglas_estilos/` (E-xx), `reglas_ux/` (UX-xx), `reglas_calidad/` (C-xx) y el catálogo `patrones/PATRONES.md`.
5. `estilos/SISTEMA_VISUAL.md` si el cambio toca interfaz.
6. `bloqueos/BLOQUEOS.md` antes de diagnosticar un fallo.

## Mapa

- `GUIA_IA.md`: protocolo para agentes IA.
- `ARQUITECTURA.md`: estructura y límites entre módulos.
- `specs/SPEC-01-layout.md`: estructura de pantalla, navegación y responsive.
- `specs/SPEC-02-hojas.md`: lista de hojas y búsqueda.
- `specs/SPEC-03-permisos.md`: permisos de una hoja: ver, dar, cambiar y quitar acceso.
- `specs/SPEC-04-personas.md`: vista por persona.
- `specs/PLANTILLA.md`: plantilla para specs nuevas.
- `decisiones/ADR.md`: decisiones de arquitectura y diseño.
- `estilos/SISTEMA_VISUAL.md`: tokens de Fluent 2, escalas, componentes y breakpoints.
- `patrones/PATRONES.md`: patrones de código y de UI/UX en uso y antipatrones.
- `reglas_programacion/REGLAS.md`: P-xx de código.
- `reglas_estilos/REGLAS.md`: E-xx de CSS y diseño visual.
- `reglas_ux/REGLAS.md`: UX-xx de interacción, textos, confirmaciones y estados.
- `reglas_calidad/REGLAS.md`: C-xx de pruebas, accesibilidad y revisión.
- `calidad/PLAN_CALIDAD.md`: qué prueba cada capa.
- `tecnologias/STACK.md`: dependencias y restricciones.
- `bloqueos/BLOQUEOS.md`: problemas conocidos.
- `bitacora/BITACORA.md`: registro de trabajo.
- Pendientes del producto: `backend/docs/REQUERIMIENTOS.md`, sección PEN-xx.

## Formato

Escritos para IA con bajo costo de tokens: listas cortas, `clave: valor`, IDs citables. Sin tablas, separadores ni adornos.
