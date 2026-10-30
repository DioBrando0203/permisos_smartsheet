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
Decisión: React Router con `/hojas/:sheetId`, `/personas/:key`, `/disenadores`, `/revision` y `/comparar`; búsqueda, pestaña y filtros en la query (`?q=`, `?tab=`).
Consecuencias: el backend debe servir `index.html` para cualquier ruta que no sea `/api`, `/assets` ni `/docs` (tarea F0 de `PLAN_IMPLEMENTACION.md`).

## ADR-05 Sin datos personales en el navegador

Fecha: 2026-10-12. Estado: vigente.
Contexto: los permisos incluyen correos y nombres de personas.
Decisión: datos sólo en memoria (TanStack Query). localStorage sólo para preferencias sin datos personales (orden, densidad).
Consecuencias: al recargar la página se vuelve a leer del backend (que tiene su propia caché).

## ADR-06 Persona reutiliza componentes de permisos

Fecha: 2026-10-12. Estado: vigente. Excepción a P-03.
Contexto: la vista por persona cambia y quita permisos igual que la vista por hoja.
Decisión: `features/people`, `features/compare` y `features/designers` importan `AccessLevelSelect`, `RemoveShareDialog` y `useShareMutations` de `features/shares` (ampliado el 2026-10-16).
Consecuencias: un solo comportamiento de edición; si una cuarta feature lo necesita, mover esos componentes a `features/shares-common`.

## ADR-07 Puertos, proxy y build servido por el backend

Fecha: 2026-10-16. Estado: vigente. Relacionada: ADR-B08 y ADR-B14 del backend.
Contexto: el backend usa 8710 o un puerto libre al azar (`python run.py`). El backend rechaza escrituras cuyo `Origin` no esté permitido; el `Origin` lo pone el navegador con la dirección de la página. Un proxy que reescribiera `Origin` dejaría pasar a cualquier sitio que llame al servidor de Vite, así que no se reescribe.
Decisión:
- Uso diario: `npm run build` y luego `python run.py`; el backend sirve `frontend/dist` en su propio puerto (mismo origen, sin CORS); `APP_PORT` ya permite ese origen aunque el puerto sea al azar.
- Desarrollo: `npm run dev` en `127.0.0.1:5710` con `strictPort: true` (si está ocupado, Vite se detiene con un mensaje claro: el 5710 es el único origen de desarrollo permitido). Proxy de `/api` y `/docs` al backend, cuya dirección se toma de `VITE_BACKEND_URL`, si no de `backend/.port` (lo escribe `run.py` al arrancar) y si no `http://127.0.0.1:8710`.
- El frontend usa siempre rutas relativas `/api/...` (K-01); `VITE_API_URL` deja de ser necesario.
Consecuencias: dos tareas en el backend antes de empezar (F0): servir `dist` con respaldo a `index.html` y escribir `backend/.port` (en `.gitignore`).

## ADR-08 Modo solo lectura en la interfaz

Fecha: 2026-10-16. Estado: vigente. Relacionada: ADR-B11 del backend.
Contexto: el usuario mantiene `APP_READ_ONLY=true`; el backend rechaza toda escritura.
Decisión: `GET /api/health` (`read_only`) se lee al arrancar y cada 60 s. Con `true`: banner fijo "Modo solo lectura: el panel no cambia nada en Smartsheet" y todo control de escritura deshabilitado con ese motivo (UX-28). Las simulaciones (copiar, quitar de varias hojas) siguen disponibles y dicen "Simulación: no se cambió nada".
Consecuencias: no se ocultan funciones; el usuario ve qué se podría hacer y por qué no está activo.

## ADR-09 Gráficos con CSS, sin librería de gráficos

Fecha: 2026-10-16. Estado: vigente.
Contexto: las vistas necesitan barras simples (carga por fase, conteos por nivel, severidades), no gráficos interactivos.
Decisión: `StatTile` (cifra con etiqueta) y `MeterBar` (barra apilada horizontal con leyenda y valores en texto) hechos con CSS y tokens. Toda cifra mostrada en una barra también aparece como número (E-17). Sin Recharts, D3 ni similares.
Consecuencias: cero dependencias y control total de accesibilidad; si más adelante hace falta un gráfico real, exige un ADR nuevo.

## ADR-10 Pruebas sin la cuenta real

Fecha: 2026-10-16. Estado: vigente. Relacionada: QB-02 del backend.
Contexto: la cuenta es real y de administrador; las pruebas no pueden leerla ni escribirla.
Decisión:
- Componentes: MSW con handlers por feature en `src/test/handlers/` y JSON sintético en `src/test/fixtures/` con la forma exacta del contrato.
- E2E: Playwright arranca el backend real con `SMARTSHEET_BASE_URL` apuntando a un Smartsheet falso local (`backend/tests/fake_smartsheet.py`, FastAPI con datos sintéticos) y `APP_READ_ONLY=false` sólo en ese proceso; el Smartsheet falso registra las escrituras recibidas para verificarlas.
Consecuencias: tarea F0 en el backend: crear el Smartsheet falso reutilizando `tests/factories.py`.

## ADR-11 Detalle de hoja con pestañas

Fecha: 2026-10-16. Estado: vigente. Precisa UX-01.
Contexto: una hoja tiene ahora permisos, auditoría, actividad, automatizaciones y calidad de datos.
Decisión: el detalle abre siempre en Permisos (UX-01 se cumple: quién tiene acceso se ve sin clics). Las demás pestañas cargan sus datos sólo al abrirse (no al entrar a la hoja) y su elección queda en `?tab=`.
Consecuencias: entrar a una hoja hace las mismas 1 o 2 lecturas de antes; lo lento (actividad, calidad) sólo se pide si se mira.

## ADR-12 Listas completas filtradas en el navegador

Fecha: 2026-10-16. Estado: vigente.
Contexto: hay 114 hojas y 49 personas; el backend ya filtra por `q`, pero cada filtro sería otra solicitud.
Decisión: `useSheets` y `usePeople` piden la lista completa una vez y filtran por texto y filtros rápidos en el navegador con `lib/search.ts` (misma regla sin tildes ni mayúsculas que el backend).
Consecuencias: búsqueda instantánea; si la cuenta llegara a miles de hojas, volver a filtrar en el backend.

## ADR-13 Mapa con Leaflet directo y teselas públicas

Fecha: 2026-10-30. Estado: vigente. Aprobada por el usuario al solicitar la implementación de PEN-29.
Contexto: SPEC-11 necesita un mapa interactivo (clic, marcador, línea resaltada). ADR-09 evita librerías visuales, pero un mapa con teselas, zoom y arrastre no se hace razonablemente con CSS. Opciones revisadas el 2026-10-30 con `npm view`: `leaflet` 1.9.4 (BSD-2-Clause, publicada 2023-05-18), `react-leaflet` 5.0.0 (licencia Hippocratic 2.1, no estándar y con restricciones de uso) y MapLibre GL (más pesada, pensada para teselas vectoriales).
Decisión:
- `leaflet` 1.9.4 y `@types/leaflet` 1.9.22 (MIT, publicada 2026-08-01), versiones exactas (P-31). Sin `react-leaflet`, por su licencia: un componente propio `components/map/MapView.tsx` crea el mapa en un `ref`, lo destruye al desmontar y expone sólo lo que el panel usa (centro, zoom, marcadores, línea, clic).
- Marcadores con `circleMarker` y líneas con `polyline` en colores de los tokens: sin imágenes de iconos de Leaflet, que se rompen al empaquetar.
- Mapa base por defecto USGS The National Map (`USGSTopo`, alternativa `USGSImageryTopo`): dominio público, sin cuenta ni clave. Verificado: teselas hasta el zoom 16 en Miami (17 y 18 dan 404); se usa `maxNativeZoom: 16` y se amplía hasta 19.
- Excepción a K-01: las teselas del mapa base las pide el navegador directo al proveedor, porque pasarlas por el backend no aporta nada y multiplicaría el tráfico. Todos los datos (vías, parcelas, jurisdicción) siguen saliendo sólo de `/api/map/...`.
- Atribución visible del proveedor del mapa base, como piden sus términos.
Consecuencias: una dependencia nueva de unos 40 KB comprimidos, cargada sólo en la ruta `/mapa` con importación diferida para no pesar en el resto del panel. Leaflet en jsdom es poco fiable: las pruebas de componente simulan `MapView` y el mapa real se prueba en E2E. OpenStreetMap queda sólo para pruebas locales (su política no admite uso comercial intenso) y Esri con clave para M6, con su propio ADR si se adopta.
