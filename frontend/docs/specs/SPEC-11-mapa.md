# SPEC-11 Mapa: vía, milepost, jurisdicción y parcela

Estado: implementada M3-M4, el buscador de M6, el trazo como en OSP (PEN-32) y los límites de parcelas (PEN-33), con E2E (2026-10-30)
Responsable del código: `features/map/`, `components/map/MapView.tsx`, `app/router.tsx`, `components/layout/AppLayout.tsx`
Relacionadas: PEN-29, ADR-13, ADR-05, SPEC-01, K-01 a K-06; backend SPEC-B14, ADR-B16, ADR-B17

## Objetivo

Hacer clic en el mapa y saber al instante sobre qué vía se está, su milepost, de quién es la calle y qué parcela hay ahí; marcar un tramo y copiar la fila que pide OSP (County, State Road ID, Section Number, Beginning y Ending Milepost) sin dibujar una solicitud en OSP.

## Alcance

- Incluye: destino "Mapa" en la navegación, ruta `/mapa`, modos Punto y Trazo, buscador (dirección, calle, ruta con milepost o coordenadas pegadas), panel de resultados, copiar datos, fuentes y avisos, estado en la URL.
- Excluye: capas de vías dibujadas, Turnpike, mapa base con clave (resto de la fase M6 de PEN-29) y cualquier escritura.

## Comportamiento

1. Navegación: sexto destino "Mapa" (icono de mapa de Fluent) después de Comparar, con `aria-current` como los demás. SPEC-01 pasa de cinco a seis destinos en M3; en 860 px o menos la barra inferior muestra los seis iconos.
2. Pantalla `/mapa`: mapa a la izquierda ocupando el alto disponible y panel de resultados a la derecha (360 px). Barra superior del mapa con:
   - selector de modo `Punto` | `Trazo` (por defecto Punto);
   - buscador "Buscar lugar" (combobox con lista de sugerencias, `MapSearchBox`): tras 350 ms sin escribir y con 3 caracteres o más pide `GET /api/map/search`; cada sugerencia muestra su tipo (Dirección, Calle, Ruta y milepost, Coordenadas) y su detalle; flechas y Enter eligen, Escape cierra la lista y, con la lista cerrada, borra el texto; `lat, lon` pegado (por ejemplo desde Google Maps) con Enter se usa sin esperar sugerencias; si una fuente no respondió, la lista lo dice; sin resultados, ejemplos de qué escribir; elegir un resultado lo marca (Punto, o A y luego B en Tramo) y centra el mapa en él con zoom 16;
   - selector de mapa base `Calles (USGS)` | `Satélite (USGS)` | `Satélite HD (NAIP, más zoom)` (PEN-31): las dos primeras son teselas fijas que llegan al zoom 16 y luego se amplían; la HD pide a USGS NAIP Plus una imagen por tesela (píxel de 30 cm), nítida hasta el zoom 19-20 pero más lenta (unos 8 s para llenar la vista a zoom 19), por eso no es la opción por defecto;
   - casilla "Vías del FDOT": superpone las vías estatales (naranja, `--map-road-state`) y de condado (verde, `--map-road-county`) que dibuja el FDOT, con su leyenda; es la línea de referencia del FDOT y puede quedar a unos metros de la calle de la foto;
   - en el mapa, escala en metros y pies; zoom máximo 20.
3. Vista inicial: centrada en el sur de Florida con zoom de condado; panel con instrucciones breves ("Haz clic sobre una calle o pega coordenadas").
4. Modo Punto: un clic pone un marcador y pide `GET /api/map/point`. El panel muestra, en este orden:
   - Vía: tipo (`Estatal`, `De condado`, `Otra`) como Badge, ruta (SR 953), nombre local, ID de vía, sección y milepost con CopyText; si hay más vías en el radio, la lista con su distancia (útil en cruces).
   - De quién es la calle: autoridad y nombre, en qué se basa y la confianza (`Alta`, `Media`, `Baja`); con confianza media o baja, el aviso "Aproximación: confirmar con el condado o la ciudad".
   - Ubicación: condado, ciudad o "Zona no incorporada", ZIP, estado (siempre Florida: el backend rechaza puntos fuera) y distrito del FDOT.
   - Parcela: ID con CopyText, uso de suelo y, si es pública, de qué tipo; propietario con la etiqueta "Según el tasador (registro público)"; "Fuente": "FDACS (datos del tasador)" o, si FDACS falló en Broward, "Condado de Broward (sólo el folio)", con uso y propietario "No disponible" (PEN-30).
   - Fuentes: cada fuente con su estado; si alguna falló, aviso con el nombre de la fuente y "Reintentar".
5. Modo Trazo (PEN-32, reemplaza al antiguo Tramo de dos puntos), como el paso 3 de OSP: cada clic (o resultado del buscador) agrega un vértice; el primero lleva la etiqueta "Inicio" y la línea a medias se ve punteada. Doble clic, Enter o "Terminar" (activo desde dos puntos) cierran el trazo y piden `GET /api/map/trace`; "Deshacer" quita el último vértice y "Borrar" o Escape lo vacían; terminado, el siguiente clic empieza otro. Mientras se dibuja, el doble clic no acerca el mapa. El panel muestra la tabla "Work Location (como en OSP)" con las columnas de OSP (County, State Road ID como ruta "SR 953" con el nombre local debajo, Section, Begin MP, End MP, Turnpike "Yes"/"No"), una fila por vía que sigue el trazo; las vías que no son estatales llevan la marca "No estatal" y una nota (OSP no las acepta). Cada fila tiene su botón de copiar (texto tabulado) y "Copiar tabla para Excel o Smartsheet" copia la tabla con los encabezados de OSP. El tramo de cada fila se resalta en el mapa. Sin vías en el trazo: aviso "Sin vías en el trazo".
6. Sin vía cerca: el panel lo dice ("No hay una vía a menos de 25 m") y muestra igual ubicación y parcela.
6b. Zona y cruce (PEN-34): selectores "Condado" ("Todo Florida" por defecto; grupo "Donde trabajamos" con Broward, Palm Beach, Martin y Miami-Dade, luego "Otros condados") y "Ciudad" (sólo municipios del condado elegido, más "Todo el condado"; deshabilitado sin condado). Elegir zona encuadra el mapa en sus límites y dibuja su contorno punteado (`map-area`); la zona se recuerda en localStorage (`map-county`, `map-city`) y la guardada no tapa la vista de una URL. Con zona, el buscador dice "Calle o dirección en {ciudad}" y busca sólo ahí; el campo "Cruce con (opcional)" convierte la búsqueda en `Calle & Cruce`. Las sugerencias distinguen "Cruce" (con el milepost si es una vía del FDOT) y "Punto más cercano" (calles que no se cruzan, con la distancia en el detalle). Elegir un resultado con vía hace que el panel muestre primero esa vía (un cruce toca dos).
7. URL compartible: `/mapa?p=lat,lon` en Punto y `/mapa?t=lat,lon;lat,lon;…` con el trazo terminado; abrir esa URL repite la consulta. Los enlaces del antiguo Tramo (`?a=…&b=…`) abren un trazo de dos puntos. Las coordenadas van con 6 decimales (la coma y el punto y coma salen codificados).
8. Datos: hooks `useMapPoint(lat, lon)`, `useMapTrace(trazo)`, `useParcelOutlines(celdas)` y `useMapSearch(texto)` con TanStack Query, claves `['map-point', lat, lon]`, `['map-trace', trazo]`, `['map-parcels', celda]` y `['map-search', texto en mayúsculas]`, `staleTime` de 10 minutos (el backend cachea una hora). El panel todavía no ofrece un "Actualizar" que pida `refresh=true` (pendiente en PEN-30).
9. Privacidad (ADR-05): el nombre del propietario sólo vive en la caché de Query y los contornos de parcelas no lo traen; la URL lleva sólo coordenadas; el mapa base y las casillas se guardan en localStorage (`map-basemap`, `map-roads`, `map-parcels`), que son preferencias sin datos (`lib/preferences.ts`).
10. Casilla "Límites de parcelas" (PEN-33): a zoom 17 o más dibuja en amarillo (`--map-parcel`) los contornos de las parcelas de la vista, pedidos por celdas fijas de 0.004 grados (`lib/cells.ts`, hasta 24 celdas) y sin repetir parcelas entre celdas; sin clic propio, el mapa sigue respondiendo debajo. Avisos junto a la casilla: "Acércate (zoom 17 o más)…", "Cargando parcelas…", "Algunas parcelas no se pudieron cargar." o "Hay demasiadas parcelas…".

## Estados

- Carga: marcador visible al instante y esqueleto en el panel; si tarda más de 3 s, LoadingNotice "Consultando FDOT y FDACS…".
- Vacío: instrucciones de uso; sin vía cerca, el mensaje del punto 6.
- Éxito: panel completo del punto o del tramo.
- Parcial: alguna fuente falló (`SOURCE_FAILED`): se muestra lo que llegó y un StatusAlert con la fuente que faltó y "Reintentar".
- Error: `COORDINATES_OUT_OF_FLORIDA` ("El punto está fuera de Florida"), `SEGMENT_ROADWAY_MISMATCH` ("A y B no están sobre la misma vía"), `SEGMENT_TOO_LONG`, `GIS_UNAVAILABLE` ("Los servicios del FDOT no responden; intenta en unos minutos"), `GIS_DISABLED`; textos en `lib/errorMessages.ts`.

## Criterios de aceptación

- CA-01: un clic en Punto muestra vía, milepost, jurisdicción, ubicación y parcela. Prueba: componente con el fixture (`MapResults.test.tsx`) y e2e con clics reales (`e2e/map.spec.ts`).
- CA-02: el trazo muestra la tabla Work Location con las columnas de OSP, una fila por vía y la marca "No estatal"; cada fila copia sus seis valores tabulados y "Copiar tabla" copia encabezados y filas. Prueba: componente con portapapeles simulado (`MapResults.test.tsx`), unidad de `lib/ospRow.ts` y e2e del trazo de control (Miami-Dade, SR 953, 281, 3.124, 3.839, No).
- CA-03: con `SOURCE_FAILED` el panel muestra los datos disponibles y la fuente que falló. Prueba: componente (`MapResults.test.tsx`, fuentes); el aviso "Datos parciales" de `MapPage` aún sin prueba.
- CA-04: cada código de error del backend muestra su texto. Prueba: pendiente (los textos están en `lib/errorMessages.ts`).
- CA-05: abrir `/mapa?p=…`, `/mapa?t=…` o un enlace viejo `/mapa?a=…&b=…` repite la consulta y deja el mapa en ese lugar. Prueba: e2e y unidad de `lib/mapUrl.ts`.
- CA-06: el buscador acepta `25.771778, -80.263610` y `25.771778 -80.263610` con Enter sin esperar sugerencias, y el parser rechaza texto que no son coordenadas. Prueba: `lib/coordinates.test.ts` y `MapSearchBox.test.tsx`.
- CA-07: el resto del panel no carga Leaflet: el bundle de `/mapa` es diferido. Prueba: revisión del build (chunk aparte).
- CA-08: el mapa real se ve y responde a clics, con las teselas externas bloqueadas en la prueba. Prueba: e2e con backend real y GIS falso.
- CA-09: sin desborde horizontal a 320 px; el panel pasa debajo del mapa. Prueba: e2e (medición de `scrollWidth` y posiciones) y revisión visual.
- CA-10: el buscador sugiere resultados con su tipo, avisa qué fuente no respondió y se maneja con teclado; elegir una ruta con milepost consulta ese punto. Prueba: `MapSearchBox.test.tsx` y e2e.
- CA-11: al abrir una URL de punto, el marcador se dibuja siempre (antes dependía del orden en que se resolvían las importaciones de Leaflet). Prueba: e2e (el clic usa la posición del marcador).
- CA-12: Ubicación muestra el estado; la parcela dice su fuente y, con el respaldo de Broward, el folio con su botón de copiar y uso y propietario "No disponible". Prueba: `MapResults.test.tsx`.
- CA-13: "Satélite HD" pide a NAIP imágenes por área cuadrada, "Vías del FDOT" pide la exportación con `dynamicLayers` y muestra la leyenda, ambas preferencias sobreviven a recargar la página y la escala tiene dos líneas (metros y pies). Prueba: e2e (servicios externos bloqueados; se verifican las solicitudes). Manual 2026-10-30 con los servicios reales en Fort Lauderdale a zoom 19: imagen nítida (barcos, palmeras, carriles) y vías en naranja.
- CA-14: el trazo se dibuja con clics y se termina con doble clic (los puntos repetidos del doble clic se descartan); "Terminar" sólo se activa con dos puntos. Prueba: e2e (clic sobre la vía y doble clic 300 m más al norte) y componente. Ver FB-08.
- CA-16: los selectores ponen primero los condados del equipo, listan sólo los municipios del condado y avisan el cambio de zona; la zona elegida encuadra el mapa. Prueba: `MapScopePicker.test.tsx` y e2e (Miami-Dade y Miami con el GIS falso: la zona no incorporada no aparece). Manual 2026-10-31 con datos reales: Broward con 31 municipios y Fort Lauderdale encuadrada con su límite.
- CA-17: con zona y "Cruce con", el buscador pide `q=Calle & Cruce` con `county` y `city`, muestra "Cruce · MP …" y al elegirlo el panel pone primero esa vía. Prueba: `MapSearchBox.test.tsx`, `MapResults.test.tsx` y e2e (NW 42nd Ave y W Flagler St en MP 3.124). Manual 2026-10-31 en Fort Lauderdale: Las Olas y 3rd Ave da "E LAS OLAS BLVD y SE 3 AVE · MP 0.258" y el panel la vía `86000142`.
- CA-15: con "Límites de parcelas", a zoom 16 se pide acercarse y a zoom 17 se piden las celdas y se dibujan los contornos. Prueba: e2e con el GIS falso y unidad de `lib/cells.ts`. Manual 2026-10-30 con servicios reales: lotes de Miami-Dade sobre "Calles" y de Broward sobre "Satélite HD".

## Accesibilidad

- El mapa es `role="application"` con nombre "Mapa"; el buscador (combobox con `aria-activedescendant` y lista `listbox`) es la alternativa completa al clic para teclado y lectores de pantalla.
- El panel de resultados es una región con título; los cambios se anuncian con `aria-live="polite"` (sólo el resumen: vía y milepost).
- Botones de zoom de Leaflet con nombre accesible en español; foco visible en todos los controles.

## Responsive

- 1180 px o menos: panel de 320 px.
- 860 px o menos: mapa arriba (60 % del alto) y panel debajo con su propio scroll; la barra del mapa se apila.

## Diseño previsto

- `components/map/MapView.tsx`: genérico, sin dominio (ADR-13): props `focus`, `markers`, `line`, `basemap`, `roads`, `onMapClick`; no importa `lib/api` ni features.
- `components/map/tileSources.ts`: mapas base y capa de vías; NAIP y FDOT no tienen teselas fijas, así que la URL lleva `{bbox}` y Leaflet llama a `tileBbox` (área de la tesela en EPSG:3857) para cada tesela.
- `features/map/`: `MapPage` (estado, modos y URL), `MapToolbar` (modos, buscador, mapa base, vías del FDOT), `MapSearchBox`, `lib/preferences.ts`, `lib/sources.ts` (nombres de fuentes), `MapResults` (`PointResult`, `MapEmpty`, `MapError`), `MapSections` (`RoadSection`, `JurisdictionSection`, `LocationSection`, `ParcelSection`, `SourcesSection`), `TraceResult` (controles y estados del trazo), `WorkLocationTable`, `useTraceDrawing` (vértices, con copia síncrona para el doble clic), `useParcelLayer` (celdas de la vista y avisos), `hooks.ts` (`useMapPoint`, `useMapTrace`, `useParcelOutlines`, `useMapSearch`), `lib/mapUrl.ts` (leer y escribir la URL), `lib/coordinates.ts` (parser), `lib/ospRow.ts` (texto para copiar), `lib/cells.ts` (celdas de parcelas).
- `MapView` importa Leaflet una sola vez y los efectos de teselas, marcadores, líneas, contornos y vista esperan a que el mapa exista (`ready`); props `lines`, `outlines`, `drawing`, `onMapDoubleClick` y `onViewChange`. Marcadores, líneas y contornos no reciben clics (`interactive: false`, FB-08).
- E2E: `e2e/map.spec.ts` contra el backend real y el GIS falso de `backend/tests/fake_gis.py` (vía sintética del caso de control).
- `lib/types.ts` y `lib/normalize.ts`: `MapPoint`, `MapSegment` y su normalización según SPEC-B14; `lib/query/keys.ts` con las claves del punto 8; `contrato/CONTRATO.md` con las dos lecturas.
- Archivos de prueba: fixtures sintéticos con propietario "PROPIETARIO SINTETICO 1" y handlers MSW en `test/handlers/map.ts`.

## Pendientes

- M5: con adaptadores de condado, la confianza "Alta" en calles locales de Palm Beach.
- M6: capas de vías estatales y de condado dibujadas, Turnpike en la fila de OSP y mapa base con más zoom (el buscador ya está).
- Encuadrar el trazo completo al abrirlo por URL: hoy la vista se centra en el primer punto con zoom 16 y el final puede quedar fuera.
- Pruebas de CA-04 y del aviso "Datos parciales" de CA-03.
- Decidir si un tramo se puede guardar o enviar a una hoja de Smartsheet: hoy no (ADR-B15, sin base de datos propia).
