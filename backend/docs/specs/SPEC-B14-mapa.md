# SPEC-B14 Mapa: vía, milepost, jurisdicción y parcela de un punto o tramo

Estado: implementada M1-M2, el buscador de M6, el trazo (PEN-32) y los límites de parcelas (PEN-33) (2026-10-30)
Código: `api/routes/map.py`, `models/map.py`, `services/map.py`, `services/map_rules.py`, `services/map_mappers.py`, `services/map_query.py`, `services/map_search.py`, `services/gis/`
Relacionadas: PEN-29, RQ-26, ADR-B15, ADR-B16, ADR-B17, SPEC-11 del frontend; investigación en `future_docs/GIS_PUBLICO_FLORIDA.md` y `future_docs/MAPAS_JURISDICCION_PARCELAS.md`

## Objetivo

Que un clic en el mapa diga sobre qué vía cae, su milepost, de quién es la calle y qué parcela hay ahí, y que dos clics den el tramo con milepost inicial y final, listo para pedir el permiso en OSP. Tipo (ADR-B15): (a) ni Smartsheet ni OSP lo dan sin dibujar una solicitud; no reemplaza OSP ni guarda nada.

## Alcance

- Incluye: consulta de punto, trazo con la tabla Work Location de OSP (y el tramo de dos puntos, que el panel ya no usa), buscador (dirección, calle, ruta con milepost o coordenadas), contornos de parcelas para dibujar y catálogo de fuentes, sólo lectura sobre servicios GIS públicos (ADR-B17).
- Excluye: dibujar capas completas, Turnpike (GIS-PEN-01), adaptadores de condado distintos de la base estatal (fase M5) y cualquier escritura.

## Fuentes verificadas (2026-10-30, GET sin sesión)

- FDOT `https://gis.fdot.gov/arcgis/rest/services/RCI_Layers/MapServer`:
  - capa 8 "LRS Basemap Routes": líneas con medida M = milepost; `ROADWAY`, `COUNTY`, `SECTION`, `BEGIN_POST`, `END_POST`, `RD_STATUS`;
  - capa 13 "Roadways with Local Names": `ROADWAY`, `NAME`, `BEGIN_POST`, `END_POST`;
  - capa 15 "State Roads": `ROADWAY`, `ROUTE` (con dobles espacios, "SR  953"), `ROUTENUM`, `DISTRICT`, `COUNTYDOT`, `COUNTY`;
  - capa 2 "County Roads": mismos campos; vacía para Broward.
- FDOT `…/Admin_Boundaries/MapServer`: capa 6 condados (`COUNTY`, `CNTYNO`, `DISTRICT`), capa 7 ciudades (`NAME`), capa 8 ZIP (`ZIP`).
- FDACS `https://gis.fdacs.gov/mapping/rest/services/GIO_Parcels_for_OAWP_Optimized/FeatureServer/0`: `CO_NO`, `PARCEL_ID`, `DOR_UC`, `OWN_NAME`.
- Buscador: geocodificador público del Censo de EE. UU. `https://geocoding.geo.census.gov/geocoder/locations/onelineaddress` (`address`, `benchmark=Public_AR_Current`, `format=json`, sin clave); responde `result.addressMatches[]` con `matchedAddress` y `coordinates` (`x` = lon, `y` = lat).
- Consulta común: `GET {capa}/query` con `geometry=lon,lat`, `geometryType=esriGeometryPoint`, `inSR=4326`, `spatialRel=esriSpatialRelIntersects`, `outFields` explícitos, `f=json`; en vías, además `distance` en metros, `units=esriSRUnit_Meter`; en la capa 8, `returnGeometry=true`, `returnM=true`, `outSR=4326`.
- Caso de control: `25.771778,-80.263610` da la vía `87281000` (SR 953, sección 281) con milepost 3.124; `25.782147,-80.264005` da 3.839. Son los valores de la fila de OSP en `future_docs/osp-milepost-paso3.png`.

## Comportamiento

1. `GET /api/map/point?lat=&lon=&radius_m=25&refresh=`:
   - valida que el punto esté en el rectángulo de Florida (lat 24.3 a 31.1, lon -87.7 a -79.8); si no, 422 `COORDINATES_OUT_OF_FLORIDA`;
   - consulta en paralelo las ocho capas con un plazo por fuente; una fuente que falla no tumba la respuesta: queda en `sources` con su estado y en `warnings`;
   - un servidor que no acepta la conexión en `gis_connect_timeout_seconds` (5) no se reintenta y se salta durante `gis_unreachable_cooldown_seconds` (120) con el mismo estado (`timeout` o `error`), para que cada clic no lo espere de nuevo (PEN-30: con FDACS caído, cada punto tardaba 60 s);
   - si fallan todas las fuentes de vías y de límites, 502 `GIS_UNAVAILABLE`;
   - responde `MapPoint`.
2. `GET /api/map/segment?start_lat=&start_lon=&end_lat=&end_lon=&radius_m=25&refresh=`:
   - resuelve cada extremo como en el punto 1;
   - elige la vía presente cerca de los dos extremos, en este orden: estatal, de condado, otra; empate, la más cercana en suma de distancias;
   - si no hay vía común, 422 `SEGMENT_ROADWAY_MISMATCH` con las vías de cada extremo en `upstream_message`;
   - si el tramo mide más de `gis_max_segment_miles` (20 por defecto), 422 `SEGMENT_TOO_LONG`;
   - responde `MapSegment` con los mileposts ordenados de menor a mayor y la geometría del tramo recortada de la capa 8.
3. `GET /api/map/sources`: catálogo fijo de fuentes (id, nombre, proveedor, URL pública, qué aporta, frecuencia de actualización, licencia o nota). No llama a ningún servicio.
4. Milepost: proyectar el punto sobre la polilínea de la capa 8 e interpolar M en el segmento más cercano; tres decimales, como OSP (`map_rules.milepost_at`).
5. Jurisdicción (`map_rules.jurisdiction`, tabla de reglas en orden):
   - vía en "State Roads": `FDOT`, base `state_road`, confianza `high`;
   - vía en "County Roads": el condado, base `county_road`, confianza `medium` (CR no siempre significa mantenida por el condado);
   - otra vía dentro de una ciudad: la ciudad, base `inside_city`, confianza `low`;
   - otra vía fuera de toda ciudad: el condado, base `unincorporated`, confianza `low`;
   - sin vía cerca: `UNKNOWN`;
   - siempre con `note` que explica que es una aproximación salvo en `high`; los adaptadores de condado (M5) podrán dar `high` con su propio campo (por ejemplo `RESP_AUTH` de Palm Beach).
6. Parcela: código de uso `DOR_UC` con etiqueta y tipo de dueño público (`map_rules.DOR_USES`): 086 condado, 087 estado, 088 federal, 089 municipal, 094 derecho de vía; el resto, `null`. Tabla por confirmar con la fuente oficial (MJ-PEN-05). Una parcela con `CO_NO` 0 y `PARCEL_ID` vacío es una vía, no un predio: se responde `parcel: null` y el aviso `PARCEL_IS_ROAD`. Respaldo (PEN-30): si FDACS falla y el condado del FDOT es Broward (`CNTYNO` 86), se pide la capa pública del condado (`gis_broward_parcels_url`, campo `FOLIO`) y la parcela llega con `parcel_id` = folio, `county_code_dor` 16, uso y propietario `null` y `source` = `broward_parcels`; su estado se agrega a `sources`. Otros condados, sin respaldo todavía.
7. `owner_name` sale tal cual de FDACS (registro público), pero nunca se registra en logs ni en errores, y en pruebas y fixtures sólo hay nombres sintéticos (ADR-B17).
8. Caché: clave `map:point:{lat:.5f}:{lon:.5f}:{radio}` y `map:segment:…` con `gis_cache_ttl_seconds` (3600 por defecto, ADR-B16); `refresh=true` la salta.
9. `GET /api/map/search?q=&refresh=` (`q` de 3 a 120 caracteres; `map_query` lo interpreta sin E/S):
   - coordenadas (`25.771778, -80.263610` o con espacio): un resultado `coordinates` sin consultar fuentes, o ninguno si caen fuera de Florida;
   - ruta con milepost (`SR 953 3.5`, `SR-953 MP 3.5`, `CR 811, 0.3` o un ID de vía de 8 dígitos con su milepost): busca en "State Roads" o "County Roads" las vías cuyo rango contiene el milepost y ubica el punto sobre la capa 8 (`point_at_milepost`); resultados `milepost`, fuente `fdot_milepost`;
   - otro texto: si empieza con número de casa, dirección en el geocodificador del Censo (se agrega ", FL" si falta el estado; sólo coincidencias dentro de Florida), fuente `census_geocoder`; además, calle por nombre en la capa 13 con el texto en mayúsculas, abreviado y sin ordinales como lo escribe FDOT (`NW 42nd Avenue` → `NW 42 AVE`), punto medio de la calle, rampas al final, fuente `fdot_streets`;
   - los filtros `where` sólo se arman con texto ya validado por expresiones regulares (sin comillas);
   - hasta 8 resultados; una fuente que falla queda en `sources` y no tumba las demás;
   - caché `map:search:{texto en mayúsculas}` con el mismo vencimiento.
10. `GET /api/map/trace?path=lat,lon;lat,lon;…&radius_m=25&refresh=` (PEN-32), como el paso 3 de OSP (`future_docs/osp-milepost-paso3.png`):
   - de 2 a `gis_trace_max_points` (100) vértices, todos en Florida y como máximo `gis_max_segment_miles`; si no, 422 `TRACE_INVALID`, `COORDINATES_OUT_OF_FLORIDA` o `SEGMENT_TOO_LONG` sin consultar fuentes;
   - vías candidatas: la capa 8 por rectángulos de unos 300 m a lo largo del trazo más el radio (`trace_rules.envelopes`), con geometría y medida M;
   - el trazo se recorre cada 10 m; cada muestra queda en la vía más cercana dentro del radio y no se cambia de vía mientras la actual siga dentro del radio, así un cruce no corta la fila; tramos de menos de 20 m se descartan y una misma vía a ambos lados de uno descartado se une (`trace_rules.runs`);
   - mileposts de cada fila: proyección de sus extremos, extendidos mientras la vía siga en el radio, para que al doblar cada fila termine y empiece en la intersección; ordenados de menor a mayor, tres decimales;
   - por atributos y sólo para las vías del trazo: estatales (capa 15) y de condado (capa 2) dan el tipo y la ruta; nombres locales (capa 13) el nombre según el milepost medio; condados (`Admin_Boundaries` capa 6, `CNTYNO IN`) el nombre del condado;
   - Turnpike: punto medio de cada fila sobre la vía contra `Admin_Boundaries` capa 13; `D8` (FTE) es Turnpike (GIS-PEN-01, verificado el 2026-10-30 en SR 821 y SR 953);
   - sin vías: 200 con `rows` vacío y `NO_ROAD_NEARBY`; filas que no son estatales: `NOT_STATE_ROAD` (OSP no las acepta); la capa 8 caída: 502 `GIS_UNAVAILABLE`; otra fuente caída: `SOURCE_FAILED` y el dato en `null`;
   - caché `map:trace:{radio}:{vértices a 6 decimales}`.
11. `GET /api/map/parcels?west=&south=&east=&north=&refresh=` (PEN-33): contornos de las parcelas que tocan una celda de hasta 0.006 grados por lado (si no, 422 `PARCEL_CELL_INVALID`); el condado del centro (capa 6) decide la fuente: Broward (`gis_broward_parcels_url`, `FOLIO`), Miami-Dade (`gis_miami_dade_parcels_url`, capa 26 de `MD_LandInformation`, `FOLIO`) y FDACS (`PARCEL_ID`) para el resto. Sólo se pide el ID, nunca el propietario; geometría simplificada a 0.000005 grados (~0,5 m) y hasta 1000 parcelas (`truncated` si se llega). Fuente caída: 502 `GIS_UNAVAILABLE`. Caché por celda.

## Contrato

`MapPoint`:
- `lat`, `lon`: los de la consulta, redondeados a 6 decimales.
- `roads`: lista de `RoadMatch` ordenada por distancia; vacía si no hay vía en el radio.
- `location`: `county` | null, `county_code_fdot` | null, `fdot_district` | null, `city` | null (null = zona no incorporada), `zip` | null.
- `parcel`: `Parcel` | null.
- `jurisdiction`: `Jurisdiction`.
- `sources`: lista de `SourceStatus`.
- `warnings`: lista de códigos.

`RoadMatch`:
- `roadway_id` ("87281000"), `county_code_fdot` ("87"), `section` ("281"), `subsection` ("000").
- `kind`: `state` | `county` | `other`.
- `route`: "SR 953" | "CR 811" | null (espacios normalizados).
- `local_name`: "LEJEUNE RD/NW 42 AVE" | null.
- `milepost` (3 decimales), `distance_m` (1 decimal), `begin_post`, `end_post`.

`Jurisdiction`: `authority` (`FDOT`, `COUNTY`, `CITY`, `PRIVATE`, `SPECIAL_DISTRICT`, `UNKNOWN`), `name` ("FDOT", "Palm Beach County", "Miami"), `basis`, `confidence` (`high`, `medium`, `low`), `note`.

`Parcel`: `parcel_id`, `county_code_dor`, `use_code`, `use_label` | null, `public_owner` (`state`, `county`, `federal`, `municipal`, `right_of_way`) | null, `owner_name` | null, `source` (`fdacs_parcels` o `broward_parcels`).

`SourceStatus`: `id` (`fdot_lrs`, `fdot_state_roads`, `fdot_county_roads`, `fdot_local_names`, `fdot_counties`, `fdot_cities`, `fdot_zip`, `fdacs_parcels` y, sólo si se usó el respaldo, `broward_parcels`), `status` (`ok`, `error`, `timeout`), `ms`.

`MapSegment`:
- `start`, `end`: `MapPoint` de cada extremo.
- `road`: `RoadMatch` de la vía elegida, con `milepost` del inicio.
- `begin_milepost`, `end_milepost`, `length_mi`.
- `geometry`: GeoJSON `LineString` en WGS84 (`[[lon, lat], …]`) del tramo entre los dos mileposts.
- `osp_row`: `county`, `state_road_id`, `section_number`, `beginning_milepost`, `ending_milepost`, en el orden de la tabla Work Location de OSP.
- `jurisdiction`, `warnings`.

`MapSearch`: `query` (el texto con espacios normalizados), `results` (lista de `SearchResult`), `sources` (`SourceStatus` de `census_geocoder`, `fdot_streets` o `fdot_milepost`; vacía con coordenadas).

`SearchResult`: `kind` (`coordinates`, `address`, `street`, `milepost`), `label`, `detail` | null, `lat`, `lon`, `roadway_id` | null, `milepost` | null.

`MapTrace`: `path` ([[lat, lon], …]), `length_mi`, `rows` (lista de `WorkLocation` en el orden del trazo), `sources` (`fdot_lrs`, `fdot_state_roads`, `fdot_county_roads`, `fdot_local_names`, `fdot_counties`, `fdot_turnpike`), `warnings`.

`WorkLocation` (columnas de Work Location en OSP): `county`, `state_road_id` (la ruta como en OSP, "SR 953"; el ID de vía si no tiene ruta), `roadway_id`, `section_number`, `beginning_milepost`, `ending_milepost`, `on_turnpike` (bool | null), `kind`, `local_name`, `length_mi`, `geometry` (LineString del tramo de la vía).

`ParcelOutlines`: `source` (`broward_parcels`, `miami_dade_parcels` o `fdacs_parcels`), `parcels` (`parcel_id`, `rings` [[[lon, lat], …], …]), `truncated`.

`osp_row.state_road_id` del tramo también es la ruta ("SR 953") desde el 2026-10-30; antes era el ID de vía, distinto de OSP.

Avisos (`warnings`): `NO_ROAD_NEARBY`, `MULTIPLE_ROADS`, `SOURCE_FAILED`, `PARCEL_IS_ROAD`, `OUTSIDE_COUNTY_DATA`.

Errores nuevos (formato de `estilos/API.md`):
- 422 `COORDINATES_OUT_OF_FLORIDA`, `SEGMENT_ROADWAY_MISMATCH`, `SEGMENT_TOO_LONG`.
- 502 `GIS_UNAVAILABLE`: ninguna fuente respondió tras los reintentos.
- 503 `GIS_DISABLED`: `APP_GIS_ENABLED=false`.
- 422 `TRACE_INVALID`: el trazo no es `lat,lon;…` o no tiene de 2 a 100 vértices.
- 422 `PARCEL_CELL_INVALID`: la celda pedida es vacía o mide más de 0.006 grados por lado.

## Diseño

- `services/gis/transport.py`: su propio `httpx.AsyncClient`, sin cabecera de autorización, con plazo `gis_timeout_seconds` (20) y de conexión `gis_connect_timeout_seconds` (5), semáforo `gis_max_concurrency` (4) y `gis_max_retries` (2) ante 5xx o tiempo de lectura agotado; sin reintentos si no conecta, y ese host se salta `gis_unreachable_cooldown_seconds` (120). Nunca reutiliza el transporte de Smartsheet: el token no debe salir hacia terceros (ADR-B16).
- `services/gis/layers.py`: catálogo de capas (id de fuente, URL base configurable, campos). Las URL base salen de `gis_fdot_base_url` y `gis_fdacs_parcels_url` para poder apuntar al GIS falso en E2E.
- `services/gis/client.py`: `query_point(layer, lat, lon, fields, radius_m, with_m)`; traduce el error JSON de ArcGIS (`{"error": {...}}` con HTTP 200) a error de fuente.
- `services/gis/mappers.py` y `types.py`: JSON de ArcGIS a `RawRoad`, `RawBoundary`, `RawParcel`, `RawRoute` (con trayectos `[lon, lat, m]`).
- `services/map_rules.py`: puro: `in_florida`, `milepost_at`, `slice_route`, `pick_segment_road`, `jurisdiction` (tabla), `DOR_USES`, `normalize_route`. Si pasa de 300 líneas, separar `milepost.py`.
- `services/map.py`: `MapService.point` y `MapService.segment`; consultas en paralelo con `asyncio.TaskGroup` y caché `TtlCache`.
- `services/map_query.py` (puro) y `services/map_search.py` (`MapSearchService`, que `MapService.search` delega): buscador del punto 9; `GisClient.query_where` y `GisClient.geocode`.
- `services/trace_rules.py` (puro: `parse_path`, `densify`, `envelopes`, `runs`) y `services/map_trace.py` (`MapTraceService`): trazo del punto 10; `GisClient.query_box` (rectángulo).
- `services/map_parcels.py` (`MapParcelsService`) y `gis/layers.parcel_outline_layer`: contornos del punto 11.
- `services/gis/timing.py` (`run_source`): mide cada fuente y la vuelve `SourceStatus` sin tumbar la respuesta; lo usan el buscador y el trazo.
- Pruebas: `tests/fake_gis.py` es el GIS falso del E2E (CA-13) y `tests/e2e_backend.py` arranca el backend apuntado a él y al Smartsheet falso, sin leer el token de `.env`.
- `models/map.py` y `api/routes/map.py`: contrato y ruta delgada, con etiqueta propia en Swagger ("mapa").
- Configuración nueva en `core/config.py`: `app_gis_enabled` (true), `gis_fdot_base_url`, `gis_fdacs_parcels_url`, `gis_census_geocoder_url`, `gis_broward_parcels_url`, `gis_miami_dade_parcels_url`, `gis_trace_max_points` (100), `gis_timeout_seconds`, `gis_connect_timeout_seconds`, `gis_unreachable_cooldown_seconds`, `gis_max_concurrency`, `gis_max_retries`, `gis_cache_ttl_seconds`, `gis_max_segment_miles`.

## Criterios de aceptación

- CA-01: el caso de control (SR 953) da `87281000`, sección `281` y milepost 3.124 y 3.839 en sus dos puntos con la geometría sintética equivalente. Prueba: `test_map_rules.py::test_milepost_control_case`.
- CA-02: `milepost_at` interpola entre vértices y elige el segmento más cercano entre varias trayectorias. Prueba: `test_map_rules.py`.
- CA-03: cada regla de jurisdicción tiene su caso, incluida la ausencia de vía. Prueba: `test_map_rules.py::test_jurisdiction_table`.
- CA-04: con una fuente caída (500 o tiempo agotado) la respuesta es 200, la fuente queda en `error` o `timeout` y aparece `SOURCE_FAILED`. Prueba: `test_map.py` con `respx`.
- CA-05: con todas las fuentes caídas, 502 `GIS_UNAVAILABLE`. Prueba: `test_map.py`.
- CA-06: punto fuera de Florida, 422 sin llamar a ninguna fuente. Prueba: `test_map.py` verifica cero llamadas.
- CA-07: tramo con vía común devuelve mileposts ordenados, `osp_row` y geometría recortada; sin vía común, 422 `SEGMENT_ROADWAY_MISMATCH`. Prueba: `test_map.py`.
- CA-08: ninguna solicitud a los servicios GIS lleva `Authorization` ni el token, aunque esté configurado. Prueba: `test_gis_transport.py` inspecciona las solicitudes de `respx`.
- CA-09: `owner_name` no aparece en los logs de una consulta. Prueba: `test_map.py` con `caplog`.
- CA-10: la segunda consulta del mismo punto sale de la caché; `refresh=true` vuelve a consultar. Prueba: `test_map.py` cuenta llamadas.
- CA-11: verificación manual con GET reales del caso de control y de un punto por condado (Broward, Palm Beach, Martin, Miami-Dade). Prueba: manual, anotada en RESULTADOS.
- CA-12: el buscador entiende coordenadas sin consultar fuentes, ruta con milepost, calle normalizada y dirección, y sobrevive a una fuente caída. Prueba: `test_map_query.py` y `test_map.py::test_search_*`.
- CA-13: el backend completo funciona contra el GIS falso que usa el E2E del frontend (punto, tramo y buscador) y ninguna solicitud lleva `Authorization`. Prueba: `test_fake_gis.py`.
- CA-14: una fuente que no conecta se intenta una sola vez y, mientras dura la pausa, el siguiente punto no la vuelve a pedir; pasada la pausa, sí. Prueba: `test_map_fallback.py`. Manual 2026-10-30 con FDACS sin conexión: de 60,8 s a 6,0 s el primer punto y 1,6 s los siguientes.
- CA-15: con FDACS caído en Broward la parcela llega del condado con `source: broward_parcels`; fuera de Broward, o con FDACS bien, no se pide el respaldo. Prueba: `test_map_fallback.py`; manual 2026-10-30: folio `494236300010` en Fort Lauderdale.
- CA-16: el trazo del caso de control da una fila igual a OSP: Miami-Dade, SR 953, 281, 3.124 a 3.839, Turnpike No. Prueba: `test_fake_gis.py`; manual 2026-10-30 con GET reales, en 1,6 s.
- CA-17: un cruce no corta la fila; al doblar a otra vía hay dos filas que se juntan en la intersección; dibujado al revés da los mismos mileposts; lejos de toda vía, sin filas. Prueba: `test_trace_rules.py`; manual 2026-10-30: SR 953 (3.126 a 3.449) y SR 968 (4.533 a 4.789), contra 3.124 y 4.534 del punto en ese cruce.
- CA-18: Turnpike con `D8`, trazo inválido, fuera de Florida o largo sin consultar fuentes, sin vías y capa 8 caída. Prueba: `test_map_trace.py`; manual 2026-10-30: SR 821 con Turnpike `true`.
- CA-19: contornos por celda desde el condado y sin propietario. Prueba: `test_fake_gis.py`; manual 2026-10-30: Broward 41 parcelas (31 KB, 1,1 s) y Miami-Dade 121 (22 KB, 0,8 s).

## Fases

- M1: punto (CA-01 a CA-06, CA-08 a CA-11).
- M2: tramo (CA-07).
- M5: pendiente: adaptadores de condado con su propia fuente de jurisdicción, empezando por Palm Beach (`ENG/CENTERLINE`, campo `RESP_AUTH`); cada uno con su spec o una sección nueva aquí.
- M6: hechos el buscador (CA-12), las vías dibujadas y la imagen HD (PEN-31, en el frontend), el Turnpike (CA-18) y los límites de parcelas (CA-19); pendiente el mapa base con clave.

## Pendientes

- Turnpike: resuelto en el trazo con la capa 13 de distritos (`D8`); falta compararlo con OSP en un tramo real del Turnpike (el `osp_row` del tramo de dos puntos no lo trae).
- Respaldo de contornos para Palm Beach (`Parcels/Parcels/MapServer`) y Martin; hoy usan FDACS, que no responde desde el equipo Windows (B-13).
- Confirmar la tabla `DOR_UC` (MJ-PEN-05).
- Confirmar con el usuario el geocodificador del Censo como fuente nueva del buscador: ADR-B17 sólo nombraba FDOT y FDACS para la fase base.
- Verificación manual del buscador con GET reales (dirección, calle y ruta con milepost): no hay evidencia registrada.
