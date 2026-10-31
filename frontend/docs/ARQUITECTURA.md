# Arquitectura del frontend

Panel React con estética Fluent 2 sobre el backend de `backend/` (28 endpoints, ver `contrato/CONTRATO.md`). Habla sólo con ese backend. Decisiones en `decisiones/ADR.md`; patrones en `patrones/PATRONES.md`; orden de construcción en `PLAN_IMPLEMENTACION.md`.

Estado: F1-F3 en curso (2026-10-30). F7: mapa base M3-M4 y buscador implementados y con E2E; M5 y el resto de M6 siguen pendientes.

## Mapa de navegación

Seis destinos en la navegación lateral, cada uno con URL propia (ADR-04):

- Hojas `/hojas`: lista maestra (SPEC-02) y detalle `/hojas/:sheetId` con pestañas (SPEC-05): Permisos (por defecto, SPEC-03), Auditoría, Actividad, Automatizaciones, Calidad de datos.
- Personas `/personas`: directorio (SPEC-04) y detalle `/personas/:key` con sus hojas y "Quitar de varias hojas".
- Diseñadores `/disenadores`: carga y acceso (SPEC-08).
- Revisión `/revision`: riesgos de la cuenta, resumen de acceso y automatizaciones de toda la cuenta (SPEC-06); referencias entre hojas (SPEC-09).
- Comparar `/comparar?a=&b=`: dos hojas lado a lado y copiar permisos con simulación (SPEC-07).
- Mapa `/mapa`: punto o tramo, milepost, jurisdicción, parcela y fila para OSP (SPEC-11).

Además: `/` redirige a `/hojas`; ruta desconocida muestra "Esta página no existe" (SPEC-01).

## Estructura

```text
src/
  main.tsx                                 QueryClientProvider, RouterProvider, global.css
  app/
    router.tsx                             rutas de los seis destinos y redirecciones
    App.tsx                                AppLayout + banner de modo solo lectura + Outlet
    styles/                                tokens.css, base.css, ui-*.css, layout.css, <feature>.css, responsive.css
  components/
    layout/AppLayout.tsx                   cabecera, navegación lateral, huecos (list, detail, toolbar)
    layout/MasterDetail.tsx                lista + detalle con su propio scroll; apilado en móvil
    ui/                                    Button, IconButton, SearchBox, Select, Tabs, Dialog, ConfirmDialog,
                                           Toast, StatusAlert, EmptyState, Spinner, Skeleton, Badge, Avatar,
                                           DataTable, StatTile, MeterBar, LoadingNotice, CopyText
  features/
    shell/                                 useHealth, useMe, ReadOnlyBanner, AccountBadge
    sheets/                                SheetList, SheetRow, SheetHeader, SheetTabs, useSheets, useSheet
    shares/                                ShareTable, ShareRow, AccessLevelSelect, ShareDialog, RecipientInput,
                                           RemoveShareDialog, LockedHint, useShares, useShareMutations,
                                           lib/groupShares.ts, lib/recipients.ts
    people/                                PeopleList, PeopleFilters, PersonDetail, RevokeDialog, usePeople,
                                           usePerson, useRevokePerson
    audit/                                 SheetAuditPanel, AlertList, DomainList, useSheetAudit
    activity/                              ActivityPanel, ChangedRowsTable, EditorsList, RowHistoryDialog,
                                           useSheetActivity, useRowHistory
    automations/                           AutomationsPanel, AutomationCard, AccountAutomations,
                                           useSheetAutomations, useAccountAutomations
    quality/                               QualityPanel, QualityForm, QualityResults, ReferencesPanel,
                                           AccountReferences, useColumns, useSheetQuality, useReferences
    review/                                ReviewPage, RiskSummary, RiskPeople, AccessSummaryTable,
                                           useAccountReview, useAccessSummary
    compare/                               ComparePage, SheetPicker, CompareResult, CopyPlanTable,
                                           useCompare, useCopyShares
    designers/                             DesignersPage, DesignerRow, DesignerDetail, PhaseBar, SheetGaps,
                                           useDesigners
    map/                                   MapRoute, MapPage, MapToolbar, MapScopePicker, MapSearchBox, MapResults, MapSections, TraceResult, WorkLocationTable, useTraceDrawing, useParcelLayer, hooks; area (zona: condado y ciudad); lib: coordenadas, URL, tabla OSP, celdas, preferencias, nombres de fuentes, etiquetas del buscador
  lib/
    api.ts                                 único punto HTTP (fetch), ApiError, timeouts
    types.ts                               contrato normalizado (espejo de backend/docs/estilos/API.md)
    normalize.ts                           JSON del backend a tipos, por endpoint
    accessLevels.ts                        orden, etiqueta, descripción e icono de cada nivel
    errorMessages.ts                       código de error a texto y acción (CONTRATO.md)
    severity.ts                            high/medium/info a etiqueta, icono y tono
    formatters.ts                          fechas relativas, plurales, números
    search.ts                              búsqueda sin tildes ni mayúsculas
    routes.ts                              constructores de URL internas (/hojas/:id, /personas/:key)
    query/keys.ts                          claves de consulta (CONTRATO.md)
    query/client.ts                        QueryClient con staleTime y reintentos
    query/invalidation.ts                  invalidateAfterShareWrite
  components/map/MapView.tsx               Leaflet genérico, importado sólo en /mapa
  components/map/tileSources.ts            mapas base (USGS, NAIP) y capa de vías del FDOT (ADR-13)
  test/
    setup.ts                               jest-dom, cleanup, servidor MSW
    handlers/                              handlers MSW por feature con datos sintéticos
    fixtures/                              JSON sintético con la forma del contrato (@example.com)
e2e/                                       Playwright contra backend real + Smartsheet y GIS falsos (ADR-10)
```

## Dependencias permitidas

- `app` importa todo.
- `features/<x>` importa `components/ui`, `components/layout`, `lib` y su propio contenido. No importa otra feature, con dos excepciones vigentes:
  - `people`, `compare` y `designers` reutilizan de `shares` el selector de nivel, el diálogo de quitar y `useShareMutations` (ADR-06).
  - `sheets/SheetTabs` monta los paneles de `shares`, `audit`, `activity`, `automations` y `quality` (es el contenedor del detalle; ADR-11).
- `components/ui` y `components/layout` no importan `features` ni `lib/api`.
- `lib` no importa React salvo `lib/query`.

## Flujo de datos

1. La URL decide la vista y los filtros compartibles (`/hojas/:sheetId?tab=actividad`, `?q=`).
2. Los hooks de cada feature leen con TanStack Query y las claves de `lib/query/keys.ts`.
3. `staleTime` de 60 s (el backend ya cachea 120 s); "Actualizar" pide `refresh=true` y reemplaza la caché.
4. Una escritura espera la respuesta; al confirmar, `invalidateAfterShareWrite` invalida lo afectado y un Toast dice qué cambió.
5. Un error se traduce con `errorMessages` por su `code` (K-03).

## Estado

- Servidor: TanStack Query, sólo en memoria (ADR-05).
- Vista compartible (pestaña, búsqueda, filtros, hojas comparadas): la URL.
- Vista local (diálogo abierto, fila expandida): estado del componente dueño.
- Preferencias sin datos personales (densidad, columnas): localStorage.
- Modo solo lectura: `useHealth().readOnly`, leído por los componentes que ofrecen escrituras (ADR-08).

## Datos de la cuenta que condicionan la interfaz (verificados en el backend)

- 114 hojas (110 del token y 4 de otra persona de sólo consulta), 49 personas en el directorio, 857 permisos aproximadamente.
- Primeras cargas: directorio 3 a 5 s; revisión de cuenta 5 s; diseñadores 14 s; automatizaciones de la cuenta 17 s; historial de una fila hasta 11 s.
- Un mismo `share.id` aparece en el permiso propio y en el heredado (B-05 del backend): la clave de fila es `id + scope`.
- Algunos permisos llegan sin nombre: se muestra el correo.
- Quien ve una hoja sólo por Dynamic View no aparece en sus permisos (B-07 del backend).
