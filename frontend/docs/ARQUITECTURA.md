# Arquitectura del frontend

Panel React con estética Fluent 2: cabecera, navegación lateral (Hojas, Personas), lista maestra y panel de detalle. Habla sólo con el backend. Decisiones en `decisiones/ADR.md`; patrones en `patrones/PATRONES.md`.

Estado: plano aprobado (2026-10-12). Ningún archivo existe todavía; se actualiza con el código.

## Estructura

```text
src/
  main.tsx                                 monta App, QueryClientProvider e importa global.css
  app/App.tsx                              rutas y composición de pantalla
  app/routes.tsx                           /hojas, /hojas/:sheetId, /personas, /personas/:key
  app/styles/                              tokens.css, base.css, ui-*.css, layout.css, features-*.css, responsive.css
  components/layout/AppLayout.tsx          cabecera, navegación, huecos list/detail/toolbar
  components/ui/                           Button, IconButton, SearchBox, Select, Dialog, ConfirmDialog,
                                           Toast, StatusAlert, EmptyState, Spinner, Skeleton, Badge, Avatar, DataTable
  features/sheets/
    components/SheetList.tsx               lista con búsqueda y conteo
    components/SheetRow.tsx                fila: nombre, nivel del token, fecha
    components/SheetHeader.tsx             cabecera del detalle: nombre, enlace a Smartsheet, actualizar
    hooks/useSheets.ts                     consulta de hojas
  features/shares/
    components/ShareTable.tsx              personas con acceso: nombre, correo, nivel, origen, acciones
    components/ShareRow.tsx                fila con selector de nivel y quitar
    components/AccessLevelSelect.tsx       selector de nivel con descripciones
    components/ShareDialog.tsx             dar acceso: destinatarios, nivel, aviso por correo
    components/RecipientInput.tsx          chips de correos y grupos con autocompletado
    components/RemoveShareDialog.tsx       confirmación de quitar acceso
    components/LockedHint.tsx              motivo de bloqueo (propietario, heredado, sin permiso)
    hooks/useShares.ts                     consulta y mutaciones con invalidación
    lib/groupShares.ts                     agrupa propio y heredado de la misma persona
    lib/recipients.ts                      validación de correos y duplicados
  features/people/
    components/PeopleList.tsx              personas y grupos con cantidad de hojas
    components/PersonDetail.tsx            hojas de una persona con nivel y acciones
    hooks/usePeople.ts
  lib/api.ts                               único punto HTTP (fetch), errores a ApiError(code)
  lib/types.ts                             contrato normalizado
  lib/normalize.ts                         JSON del backend a tipos
  lib/accessLevels.ts                      orden, etiqueta, descripción e icono de cada nivel
  lib/errorMessages.ts                     código de error a texto y acción
  lib/formatters.ts                        fechas relativas, plurales
  lib/search.ts                            búsqueda sin tildes ni mayúsculas
  lib/query/                               claves de consulta y cliente de TanStack Query
e2e/                                       Playwright contra el backend con Smartsheet simulado
```

## Dependencias permitidas

- `app` importa todo.
- `features/<x>` importa `components/ui`, `lib` y su propio contenido. No importa otra feature, salvo `people` que reutiliza `shares/components/AccessLevelSelect` y `RemoveShareDialog` (ADR-06).
- `components/ui` y `components/layout` no importan `features` ni `lib/api`.
- `lib` no importa React salvo `lib/query`.

## Flujo de datos

1. La URL decide la vista (`/hojas/:sheetId`), para poder compartir un enlace a una hoja y usar Atrás del navegador (ADR-04).
2. Los hooks de feature leen con TanStack Query: caché por clave (`['sheets']`, `['shares', sheetId]`, `['people']`), reintento ante errores de red y estado de carga.
3. Una mutación (dar, cambiar, quitar) espera la respuesta del backend; al confirmar, invalida `['shares', sheetId]`, `['sheets']` y `['people']` y muestra un aviso (Toast).
4. Un error se traduce con `errorMessages` por su `code`, nunca mostrando el mensaje técnico como única información.

## Estado

- Servidor (permisos, hojas, personas): TanStack Query.
- Vista (búsqueda, filtros, diálogo abierto): estado local del componente dueño o la URL (`?q=`).
- Preferencias sin datos personales (orden de columnas): localStorage (ADR-05).
