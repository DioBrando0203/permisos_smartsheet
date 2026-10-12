# Decisiones de arquitectura y diseño (frontend)

Formato: contexto, decisión, consecuencias. Una decisión sólo se reemplaza con otra que la cite.

## ADR-01 Fluent 2 como sistema visual

Fecha: 2026-10-12. Estado: vigente.
Contexto: el proyecto de referencia (`extractor_metadata`) usa Fluent 2 con tokens propios e iconos MIT; el equipo ya conoce ese estilo y Microsoft 365 Admin es una referencia natural para un panel de permisos.
Decisión: tokens de Fluent 2 en CSS propio e iconos de `@fluentui/react-icons`; sin la librería de componentes `@fluentui/react-components` en la primera versión.
Consecuencias: CSS propio controlado y ligero; componentes base escritos a mano en `components/ui` (los mismos del proyecto de referencia, reutilizables).

## ADR-02 TanStack Query para datos del servidor

Fecha: 2026-10-12. Estado: vigente.
Contexto: a diferencia del proyecto de referencia, aquí hay muchas lecturas y escrituras que deben invalidarse entre vistas (hoja, persona, lista).
Decisión: TanStack Query para consultas y mutaciones; claves centralizadas en `lib/query/keys.ts`.
Consecuencias: caché, reintentos y estados de carga sin código propio; una dependencia más justificada en STACK.

## ADR-03 Escrituras pesimistas

Fecha: 2026-10-12. Estado: vigente.
Contexto: un permiso mostrado como dado y que luego falla puede hacer creer a alguien que una persona tiene o no acceso.
Decisión: la UI muestra el cambio sólo cuando el backend lo confirma; mientras, la fila queda bloqueada con indicador (UX-05).
Consecuencias: cada cambio tarda lo que tarda Smartsheet (normalmente menos de 2 s); a cambio, lo que se ve es siempre real.

## ADR-04 Rutas con React Router

Fecha: 2026-10-12. Estado: vigente.
Contexto: el equipo querrá compartir el enlace a una hoja o persona y usar Atrás.
Decisión: React Router con `/hojas/:sheetId` y `/personas/:key`; búsqueda en `?q=`.
Consecuencias: el backend debe servir `index.html` para cualquier ruta que no sea `/api` ni `/assets`.

## ADR-05 Sin datos personales en el navegador

Fecha: 2026-10-12. Estado: vigente.
Contexto: los permisos incluyen correos y nombres de personas.
Decisión: datos sólo en memoria (TanStack Query). localStorage sólo para preferencias sin datos personales (orden, densidad).
Consecuencias: al recargar la página se vuelve a leer del backend (que tiene su propia caché).

## ADR-06 Persona reutiliza componentes de permisos

Fecha: 2026-10-12. Estado: vigente. Excepción a P-03.
Contexto: la vista por persona cambia y quita permisos igual que la vista por hoja.
Decisión: `features/people` importa `AccessLevelSelect` y `RemoveShareDialog` de `features/shares` y el hook de mutaciones `useShareMutations`.
Consecuencias: un solo comportamiento de edición; si crece, mover esos componentes a una feature compartida.
