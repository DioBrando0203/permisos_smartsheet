# Resultados verificados (frontend)

Sólo ejecuciones reales, con fecha America/Lima (C-13).

## 2026-10-16 16:38 -05:00 F0

- `npm run build`: pasa. TypeScript estricto y Vite completaron el build de producción.
- `npm run lint`: pasa, sin errores ni warnings.
- `npm test`: pasa. 1 archivo y 1 prueba: cliente HTTP y normalización de `/api/health` con MSW.
- `npm run format:check`: pasa.
- `npm audit --omit=dev` y `npm audit`: pasan, 0 vulnerabilidades.

## 2026-10-16 16:56 -05:00 Revisión F0

- `npm run build`: pasa con la resolución automática de `frontend/.env` y con `VITE_BACKEND_URL=http://127.0.0.1:8710`.
- `npm run lint`: pasa, sin errores ni warnings.
- `npm test`: pasa. 1 archivo y 4 pruebas: éxito, error de backend, 422 y backend inaccesible con MSW.
- `npm run format:check`: pasa.
- `npm audit --omit=dev` y `npm audit`: pasan, 0 vulnerabilidades.

## 2026-10-16 17:17 -05:00 Corrección de runners de prueba

- `npm run build`, `npm run lint`, `npm test` (4 pruebas) y `npm run format:check`: pasan.
- `npm run test:e2e`: pasa. 1 caso marcado omitido: F1 define el primer flujo funcional.
- `npm run test:visual`: pasa. 1 caso marcado omitido: F6 define las primeras capturas.

## 2026-10-27 16:17 -05:00 F1 en curso

- `npm run build`, `npm run lint` y `npm run format:check`: pasan.
- `npm test`: pasa. 4 archivos y 8 pruebas, incluidas búsqueda, permisos propio/heredado y vistas de hojas con MSW.
- `npm run test:e2e`: pasa con el caso F0 omitido; el flujo E2E real de F1 sigue pendiente.

## 2026-10-28 10:10 -05:00 F2 en curso

- `npm run build`, `npm run lint` y `npm run format:check`: pasan.
- `npm test`: pasa. 5 archivos y 10 pruebas, incluidas los filtros y orden del directorio de personas.
- `npm run test:e2e`: pasa con el caso F0 omitido; los flujos funcionales siguen pendientes.

## 2026-10-28 10:28 -05:00 Corrección de arranque

- Comprobación en navegador de `http://127.0.0.1:5710/hojas`: pasa. Se renderiza la lista de hojas y no se registran errores de JavaScript.
- Proxy de desarrollo `GET /api/health`: responde 200.
- `npm run build`, `npm run lint`, `npm test` (5 archivos y 10 pruebas) y `npm run format:check`: pasan.

## 2026-10-28 10:46 -05:00 F3 en curso

- `npm run build`, `npm run lint`, `npm test` (6 archivos y 12 pruebas) y `npm run format:check`: pasan.
- `npm run test:e2e`: pasa con el único caso F0 aún omitido.
- Revisión visual de Auditoría en 320, 390, 1024, 1440 y 1920 px: sin desborde horizontal; las pestañas siguen presentes en todos los anchos.

## 2026-10-28 12:27 -05:00 CRUD base de permisos

- `npm run build`, `npm run lint`, `npm test` (7 archivos y 14 pruebas) y `npm run format:check`: pasan.
- Las pruebas unitarias cubren la respuesta `204` de eliminación y el análisis de correos pegados, incluidos duplicados.
- No se ejecutaron `POST`, `PATCH` ni `DELETE` contra el backend real ni Smartsheet; las mutaciones permanecen deshabilitadas con `APP_READ_ONLY=true`.

## 2026-10-28 15:35 -05:00 Autocompletado de permisos

- `npm run build`, `npm run lint`, `npm test` (7 archivos y 15 pruebas), `npm run test:e2e` (1 omitida) y `npm run format:check`: pasan.
- Fixtures y normalizadores de contactos y grupos verificados sin acceder a la cuenta real.
- `sheets.css` y el nuevo `shares.css` respetan el máximo de 250 líneas por archivo.

## 2026-10-28 17:32 -05:00 Detalle y simulación de personas

- `npm run build`, `npm run lint`, `npm test` (8 archivos y 16 pruebas), `npm run test:e2e` (1 omitida) y `npm run format:check`: pasan.
- Revisión visual del detalle de persona a 320, 390, 1024, 1440 y 1920 px: sin desborde horizontal y el detalle permanece disponible.
- La prueba de contrato verifica que el plan de revocación conserva sus hojas y motivos de omisión; no se ejecutó una revocación real.
# 2026-10-30 Mapa GIS (F7, M3-M4)

- `npm run format:check`, `npm run build`, `npm run lint` y `npm test`: pasaron; Vitest: 9 archivos y 18 pruebas.
- `npm run test:e2e`: ejecutable, 1 caso F0 omitido; todavía no existe E2E funcional del mapa.
- El build separa `MapPage` y `leaflet-src` del bundle principal; Leaflet sólo se carga en `/mapa`.
- `npm audit --omit=dev` y `npm audit`: 0 vulnerabilidades tras actualizar Vite 8.3.5.

## 2026-10-30 19:27 -05:00 E2E del mapa y corrección del marcador (F7)

- Equipo nuevo (Windows 11, Node 24.19.0, npm 11.17.0): `npm ci` desde el lock; Chromium de Playwright 1.63 instalado en la caché de usuario junto a las versiones de otros proyectos, sin reemplazarlas.
- Antes de los cambios: `npm run format:check`, `npm run build`, `npm run lint` y `npm test` (11 archivos y 22 pruebas): pasaron.
- `e2e/map.spec.ts` con backend real (`tests.e2e_backend`), Smartsheet falso y GIS falso: la prueba del clic falló de forma intermitente; reproducido con una prueba temporal: 4 de 8 aperturas de `/mapa?p=…` sin marcador (FB-07). Tras la corrección de `MapView`: 12 de 12 con marcador.
- Después: `npm run format:check`, `npm run build`, `npm run lint`, `npm test` (11 archivos y 22 pruebas) y `npm run test:e2e` (4 pasan, 1 caso F0 omitido): pasaron. Suite E2E repetida 4 veces (`--repeat-each 4`): 16 de 16.
- El build sigue separando `MapPage` y `leaflet-src` del bundle principal.
- Revisión visual del tramo de control a 320, 1024 y 1440 px con teselas bloqueadas: sin desborde horizontal; a 320 px el panel queda debajo del mapa y la barra inferior muestra seis destinos. Observación: B queda fuera de la vista al abrir el tramo por URL (pendiente en SPEC-11).
- Ninguna prueba habló con Smartsheet ni con servicios GIS reales.

## 2026-10-30 20:28 -05:00 Vista del mapa (PEN-31) y parcela de respaldo (PEN-30)

- Verificado antes de programar: USGS NAIP Plus (`exportImage`, píxel de 30 cm) da a zoom 18 autos y marcas de carril en Fort Lauderdale, contra la tesela USGS de zoom 16; la exportación del FDOT con `dynamicLayers` dibuja vías estatales en naranja en 0,7 s; FDOT no publica WMS (400).
- `npm run format:check`, `npm run build`, `npm run lint` (sin avisos), `npm test` (11 archivos y 23 pruebas) y `npm run test:e2e` (5 pasan, 1 caso F0 omitido): pasaron. Leaflet sigue en su chunk aparte.
- Manual con el servidor de desarrollo y los servicios reales, a 1440 px y zoom 19 en Fort Lauderdale: Satélite HD nítido, vías del FDOT con leyenda, escala 20 m / 50 ft, Estado "Florida" y parcela `494236300010` con fuente "Condado de Broward (sólo el folio)". La vista HD tardó 8,1 s en cargar todas las imágenes; los fallos `net::ERR_ABORTED` fueron imágenes canceladas por Leaflet al cambiar de zoom.
- `map.css` dividido: barra y buscador en `map-toolbar.css` (120 y 162 líneas, E-05).
