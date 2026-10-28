# Documentación del frontend

Fuente de verdad del panel de permisos. Metodología: desarrollo guiado por especificaciones (SDD). Ningún cambio de comportamiento entra sin spec; ninguna spec queda sin pruebas que la verifiquen.

Estado (2026-10-28): F0 terminada; F1, F2 y F3 en curso por solicitud del usuario. Ya se puede navegar, listar hojas, ver permisos, consultar el directorio y abrir Auditoría, Actividad y Automatizaciones de cada hoja en solo lectura; faltan los criterios restantes de las fases. Las specs activas están aprobadas y se marcan implementadas al cerrar cada fase.

## Orden de lectura para una IA o persona nueva

1. `GUIA_IA.md`: protocolo de trabajo, definición de terminado y prohibiciones. Obligatorio.
2. `PLAN_IMPLEMENTACION.md`: en qué fase estamos y qué toca.
3. `ARQUITECTURA.md`: navegación, módulos, dependencias permitidas, flujo de datos y estado.
4. `contrato/CONTRATO.md`: endpoint, hook, caché, invalidación y textos de error.
5. La spec del área afectada en `specs/`.
6. Las reglas: `reglas_programacion/` (P-xx), `reglas_estilos/` (E-xx), `reglas_ux/` (UX-xx), `reglas_calidad/` (C-xx) y el catálogo `patrones/PATRONES.md`.
7. `estilos/SISTEMA_VISUAL.md` si el cambio toca interfaz.
8. `bloqueos/BLOQUEOS.md` antes de diagnosticar un fallo y al empezar cada fase.

## Mapa

- `GUIA_IA.md`: protocolo para agentes IA.
- `PLAN_IMPLEMENTACION.md`: fases F0 a F6 con su definición de terminado.
- `ARQUITECTURA.md`: navegación, estructura y límites entre módulos.
- `contrato/CONTRATO.md`: cómo consume el frontend cada endpoint del backend.
- `specs/SPEC-01-layout.md`: estructura, navegación, modo solo lectura y errores globales.
- `specs/SPEC-02-hojas.md`: lista de hojas de toda la organización, búsqueda y exportación.
- `specs/SPEC-03-permisos.md`: permisos de una hoja: ver, dar, cambiar y quitar acceso.
- `specs/SPEC-04-personas.md`: directorio, detalle de persona y quitar de varias hojas.
- `specs/SPEC-05-detalle-hoja.md`: cabecera y pestañas Auditoría, Actividad y Automatizaciones.
- `specs/SPEC-06-revision.md`: riesgos, acceso por hoja y automatizaciones de toda la cuenta.
- `specs/SPEC-07-comparar.md`: comparar dos hojas y copiar permisos con simulación.
- `specs/SPEC-08-disenadores.md`: carga y acceso de los diseñadores.
- `specs/SPEC-09-calidad.md`: calidad de datos de una hoja y referencias entre hojas.
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
