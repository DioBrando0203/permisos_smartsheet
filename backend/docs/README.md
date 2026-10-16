# Documentación del backend

Fuente de verdad del servicio que lee y modifica permisos de hojas de Smartsheet. Metodología: desarrollo guiado por especificaciones (SDD), igual que el frontend. Ningún cambio de comportamiento entra sin spec; ninguna spec queda sin prueba.

## Orden de lectura para una IA o persona nueva

1. `GUIA_IA.md`: protocolo, definición de terminado y prohibiciones. Obligatorio.
2. `ARQUITECTURA.md`: capas, paquetes, dependencias permitidas, flujos y contrato.
3. La spec afectada en `specs/`.
4. `reglas_programacion/REGLAS.md` (PY-xx, SM-xx) y `patrones/PATRONES.md` antes de escribir código.
5. `bloqueos/BLOQUEOS.md` antes de diagnosticar un fallo.

## Mapa

- `GUIA_IA.md`: protocolo para agentes IA.
- `ARQUITECTURA.md`: estructura y límites entre módulos.
- `REQUERIMIENTOS.md`: requisitos verificables (RQ-xx), límites honestos y backlog priorizado (PEN-xx) con su estado.
- `specs/SPEC-B01-hojas.md`: listado y detalle de hojas.
- `specs/SPEC-B02-permisos.md`: CRUD de permisos de una hoja.
- `specs/SPEC-B03-usuarios.md`: personas con acceso y sus hojas (vista por usuario).
- `specs/SPEC-B04-cliente-smartsheet.md`: cliente HTTP, reintentos, paginación, errores y caché.
- `specs/SPEC-B05-auditoria.md`: auditoría de una hoja, comparación de hojas y resumen de acceso.
- `specs/SPEC-B06-operaciones-masivas.md`: copiar permisos y quitar accesos en bloque, con simulación.
- `specs/SPEC-B07-revision-cuenta.md`: revisión de riesgos de toda la cuenta.
- `specs/SPEC-B08-actividad.md`: actividad de una hoja e historial de filas, directo de Smartsheet.
- `specs/SPEC-B09-calidad-datos.md`: repetidos, vacíos y formato en columnas de una hoja.
- `specs/SPEC-B10-automatizaciones.md`: salud de las alertas y flujos de Smartsheet.
- `decisiones/ADR.md`: decisiones con contexto y consecuencias.
- `reglas_programacion/REGLAS.md`: código limpio (PY-xx) y reglas de Smartsheet (SM-xx).
- `patrones/PATRONES.md`: patrones de diseño en uso, cuándo aplicarlos y antipatrones.
- `reglas_estilos/REGLAS.md`: nombres, formato, docstrings y mensajes.
- `reglas_calidad/REGLAS.md`: pruebas y revisión.
- `estilos/API.md`: convenciones del contrato HTTP, endpoints y códigos de error.
- `tecnologias/STACK.md`: dependencias y fuentes primarias.
- `calidad/PLAN_CALIDAD.md`: qué prueba cada archivo de tests.
- `calidad/RESULTADOS.md`: última ejecución verificada.
- `bloqueos/BLOQUEOS.md`: problemas conocidos.
- `bitacora/BITACORA.md`: registro de trabajo.

## Formato

Escritos para IA con bajo costo de tokens: listas, `clave: valor`, IDs citables. Sin tablas, separadores ni relleno. Plantilla de spec compartida: `frontend/docs/specs/PLANTILLA.md`.
