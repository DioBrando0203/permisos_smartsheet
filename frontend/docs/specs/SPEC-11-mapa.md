# SPEC-11 Mapa: vía, milepost, jurisdicción y parcela

Estado: borrador (2026-10-30)
Responsable del código (previsto): `features/map/`, `components/map/MapView.tsx`, `app/router.tsx`, `components/layout/AppLayout.tsx`
Relacionadas: PEN-29, ADR-13, ADR-05, SPEC-01, K-01 a K-06; backend SPEC-B14, ADR-B16, ADR-B17

## Objetivo

Hacer clic en el mapa y saber al instante sobre qué vía se está, su milepost, de quién es la calle y qué parcela hay ahí; marcar un tramo y copiar la fila que pide OSP (County, State Road ID, Section Number, Beginning y Ending Milepost) sin dibujar una solicitud en OSP.

## Alcance

- Incluye: destino "Mapa" en la navegación, ruta `/mapa`, modos Punto y Tramo, coordenadas pegadas, panel de resultados, copiar datos, fuentes y avisos, estado en la URL.
- Excluye: búsqueda por dirección, capas de vías dibujadas, Turnpike, mapa base con clave (fase M6 de PEN-29) y cualquier escritura.

## Comportamiento

1. Navegación: sexto destino "Mapa" (icono de mapa de Fluent) después de Comparar, con `aria-current` como los demás. SPEC-01 pasa de cinco a seis destinos en M3; en 860 px o menos la barra inferior muestra los seis iconos.
2. Pantalla `/mapa`: mapa a la izquierda ocupando el alto disponible y panel de resultados a la derecha (360 px). Barra superior del mapa con:
   - selector de modo `Punto` | `Tramo` (por defecto Punto);
   - campo "Coordenadas" que acepta `lat, lon` pegado (por ejemplo desde Google Maps) y la tecla Enter;
   - selector de mapa base `Calles (USGS)` | `Satélite (USGS)`.
3. Vista inicial: centrada en el sur de Florida con zoom de condado; panel con instrucciones breves ("Haz clic sobre una calle o pega coordenadas").
4. Modo Punto: un clic pone un marcador y pide `GET /api/map/point`. El panel muestra, en este orden:
   - Vía: tipo (`Estatal`, `De condado`, `Otra`) como Badge, ruta (SR 953), nombre local, ID de vía, sección y milepost con CopyText; si hay más vías en el radio, la lista con su distancia (útil en cruces).
   - De quién es la calle: autoridad y nombre, en qué se basa y la confianza (`Alta`, `Media`, `Baja`); con confianza media o baja, el aviso "Aproximación: confirmar con el condado o la ciudad".
   - Ubicación: condado, ciudad o "Zona no incorporada", ZIP y distrito del FDOT.
   - Parcela: ID con CopyText, uso de suelo y, si es pública, de qué tipo; propietario con la etiqueta "Según el tasador (registro público)".
   - Fuentes: cada fuente con su estado; si alguna falló, aviso con el nombre de la fuente y "Reintentar".
5. Modo Tramo: primer clic marca A, segundo clic marca B y pide `GET /api/map/segment`; el tramo se resalta en el mapa con la geometría recibida. El panel muestra la vía, milepost inicial y final, longitud, de quién es y el bloque "Fila para OSP" con los cinco valores y el botón "Copiar para OSP" (texto separado por tabulaciones, para pegar en una tabla). Un tercer clic empieza un tramo nuevo; Escape cancela el tramo a medias.
6. Sin vía cerca: el panel lo dice ("No hay una vía a menos de 25 m") y muestra igual ubicación y parcela.
7. URL compartible: `/mapa?p=lat,lon&z=` en Punto y `/mapa?a=lat,lon&b=lat,lon&z=` en Tramo; abrir esa URL repite la consulta. Las coordenadas van con 6 decimales.
8. Datos: hooks `useMapPoint(lat, lon)` y `useMapSegment(a, b)` con TanStack Query, claves `['map-point', lat, lon]` y `['map-segment', a, b]`, `staleTime` de 10 minutos (el backend cachea una hora). "Actualizar" en el panel pide `refresh=true`.
9. Privacidad (ADR-05): el nombre del propietario sólo vive en la caché de Query; la URL lleva sólo coordenadas y el mapa base elegido se guarda en localStorage.

## Estados

- Carga: marcador visible al instante y esqueleto en el panel; si tarda más de 3 s, LoadingNotice "Consultando FDOT y FDACS…".
- Vacío: instrucciones de uso; sin vía cerca, el mensaje del punto 6.
- Éxito: panel completo del punto o del tramo.
- Parcial: alguna fuente falló (`SOURCE_FAILED`): se muestra lo que llegó y un StatusAlert con la fuente que faltó y "Reintentar".
- Error: `COORDINATES_OUT_OF_FLORIDA` ("El punto está fuera de Florida"), `SEGMENT_ROADWAY_MISMATCH` ("A y B no están sobre la misma vía"), `SEGMENT_TOO_LONG`, `GIS_UNAVAILABLE` ("Los servicios del FDOT no responden; intenta en unos minutos"), `GIS_DISABLED`; textos en `lib/errorMessages.ts`.

## Criterios de aceptación

- CA-01: un clic en Punto muestra vía, milepost, jurisdicción, ubicación y parcela del fixture. Prueba: componente con MSW y `MapView` simulado.
- CA-02: Tramo con dos clics muestra milepost inicial menor o igual que el final y "Copiar para OSP" copia los cinco valores separados por tabulaciones. Prueba: componente con MSW y portapapeles simulado.
- CA-03: con `SOURCE_FAILED` el panel muestra los datos disponibles y el aviso con la fuente que falló. Prueba: componente con MSW.
- CA-04: cada código de error del backend muestra su texto. Prueba: componente con MSW.
- CA-05: abrir `/mapa?p=…` o `/mapa?a=…&b=…` repite la consulta y deja el mapa en ese lugar. Prueba: e2e.
- CA-06: "Coordenadas" acepta `25.771778, -80.263610`, `25.771778 -80.263610` y rechaza texto inválido con un mensaje junto al campo. Prueba: unidad de `lib/mapUrl.ts` o del parser de coordenadas.
- CA-07: el resto del panel no carga Leaflet: el bundle de `/mapa` es diferido. Prueba: revisión del build (chunk aparte).
- CA-08: el mapa real se ve y responde a clics, con las teselas externas bloqueadas en la prueba. Prueba: e2e con backend real y GIS falso.
- CA-09: sin desborde horizontal a 320 px; el panel pasa debajo del mapa. Prueba: e2e visual.

## Accesibilidad

- El mapa es `role="application"` con nombre "Mapa"; el campo "Coordenadas" es la alternativa completa al clic para teclado y lectores de pantalla.
- El panel de resultados es una región con título; los cambios se anuncian con `aria-live="polite"` (sólo el resumen: vía y milepost).
- Botones de zoom de Leaflet con nombre accesible en español; foco visible en todos los controles.

## Responsive

- 1180 px o menos: panel de 320 px.
- 860 px o menos: mapa arriba (60 % del alto) y panel debajo con su propio scroll; la barra del mapa se apila.

## Diseño previsto

- `components/map/MapView.tsx`: genérico, sin dominio (ADR-13): props `center`, `zoom`, `basemap`, `markers`, `line`, `onMapClick`, `onViewChange`; no importa `lib/api` ni features.
- `features/map/`: `MapPage`, `MapToolbar`, `CoordinateInput`, `PointPanel`, `SegmentPanel`, `RoadSection`, `JurisdictionSection`, `LocationSection`, `ParcelSection`, `SourcesSection`, `useMapPoint`, `useMapSegment`, `lib/mapUrl.ts` (leer y escribir la URL), `lib/coordinates.ts` (parser), `lib/ospRow.ts` (texto para copiar).
- `lib/types.ts` y `lib/normalize.ts`: `MapPoint`, `MapSegment` y su normalización según SPEC-B14; `lib/query/keys.ts` con las claves del punto 8; `contrato/CONTRATO.md` con las dos lecturas.
- Archivos de prueba: fixtures sintéticos con propietario "PROPIETARIO SINTETICO 1" y handlers MSW en `test/handlers/map.ts`.

## Pendientes

- M5: con adaptadores de condado, la confianza "Alta" en calles locales de Palm Beach.
- M6: búsqueda por dirección, capas de vías estatales y de condado dibujadas, Turnpike en la fila de OSP y mapa base con más zoom.
- Decidir si un tramo se puede guardar o enviar a una hoja de Smartsheet: hoy no (ADR-B15, sin base de datos propia).
