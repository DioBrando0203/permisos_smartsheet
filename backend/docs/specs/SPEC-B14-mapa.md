# SPEC-B14 Mapa: vía, milepost, jurisdicción y parcela de un punto o tramo

Estado: implementada M1-M2 (2026-10-30)
Código previsto: `api/routes/map.py`, `models/map.py`, `services/map.py`, `services/map_rules.py`, `services/gis/`
Relacionadas: PEN-29, RQ-26, ADR-B15, ADR-B16, ADR-B17, SPEC-11 del frontend; investigación en `future_docs/GIS_PUBLICO_FLORIDA.md` y `future_docs/MAPAS_JURISDICCION_PARCELAS.md`

## Objetivo

Que un clic en el mapa diga sobre qué vía cae, su milepost, de quién es la calle y qué parcela hay ahí, y que dos clics den el tramo con milepost inicial y final, listo para pedir el permiso en OSP. Tipo (ADR-B15): (a) ni Smartsheet ni OSP lo dan sin dibujar una solicitud; no reemplaza OSP ni guarda nada.

## Alcance

- Incluye: consulta de punto, consulta de tramo y catálogo de fuentes, sólo lectura sobre servicios GIS públicos (ADR-B17).
- Excluye: dibujar capas completas, búsqueda por dirección, Turnpike (GIS-PEN-01), adaptadores de condado distintos de la base estatal (fase M5) y cualquier escritura.

## Fuentes verificadas (2026-10-30, GET sin sesión)

- FDOT `https://gis.fdot.gov/arcgis/rest/services/RCI_Layers/MapServer`:
  - capa 8 "LRS Basemap Routes": líneas con medida M = milepost; `ROADWAY`, `COUNTY`, `SECTION`, `BEGIN_POST`, `END_POST`, `RD_STATUS`;
  - capa 13 "Roadways with Local Names": `ROADWAY`, `NAME`, `BEGIN_POST`, `END_POST`;
  - capa 15 "State Roads": `ROADWAY`, `ROUTE` (con dobles espacios, "SR  953"), `ROUTENUM`, `DISTRICT`, `COUNTYDOT`, `COUNTY`;
  - capa 2 "County Roads": mismos campos; vacía para Broward.
- FDOT `…/Admin_Boundaries/MapServer`: capa 6 condados (`COUNTY`, `CNTYNO`, `DISTRICT`), capa 7 ciudades (`NAME`), capa 8 ZIP (`ZIP`).
- FDACS `https://gis.fdacs.gov/mapping/rest/services/GIO_Parcels_for_OAWP_Optimized/FeatureServer/0`: `CO_NO`, `PARCEL_ID`, `DOR_UC`, `OWN_NAME`.
- Consulta común: `GET {capa}/query` con `geometry=lon,lat`, `geometryType=esriGeometryPoint`, `inSR=4326`, `spatialRel=esriSpatialRelIntersects`, `outFields` explícitos, `f=json`; en vías, además `distance` en metros, `units=esriSRUnit_Meter`; en la capa 8, `returnGeometry=true`, `returnM=true`, `outSR=4326`.
- Caso de control: `25.771778,-80.263610` da la vía `87281000` (SR 953, sección 281) con milepost 3.124; `25.782147,-80.264005` da 3.839. Son los valores de la fila de OSP en `future_docs/osp-milepost-paso3.png`.

## Comportamiento

1. `GET /api/map/point?lat=&lon=&radius_m=25&refresh=`:
   - valida que el punto esté en el rectángulo de Florida (lat 24.3 a 31.1, lon -87.7 a -79.8); si no, 422 `COORDINATES_OUT_OF_FLORIDA`;
   - consulta en paralelo las ocho capas con un plazo por fuente; una fuente que falla no tumba la respuesta: queda en `sources` con su estado y en `warnings`;
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
6. Parcela: código de uso `DOR_UC` con etiqueta y tipo de dueño público (`map_rules.DOR_USES`): 086 condado, 087 estado, 088 federal, 089 municipal, 094 derecho de vía; el resto, `null`. Tabla por confirmar con la fuente oficial (MJ-PEN-05). Una parcela con `CO_NO` 0 y `PARCEL_ID` vacío es una vía, no un predio: se responde `parcel: null` y el aviso `PARCEL_IS_ROAD`.
7. `owner_name` sale tal cual de FDACS (registro público), pero nunca se registra en logs ni en errores, y en pruebas y fixtures sólo hay nombres sintéticos (ADR-B17).
8. Caché: clave `map:point:{lat:.5f}:{lon:.5f}:{radio}` y `map:segment:…` con `gis_cache_ttl_seconds` (3600 por defecto, ADR-B16); `refresh=true` la salta.

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

`Parcel`: `parcel_id`, `county_code_dor`, `use_code`, `use_label` | null, `public_owner` (`state`, `county`, `federal`, `municipal`, `right_of_way`) | null, `owner_name` | null.

`SourceStatus`: `id` (`fdot_lrs`, `fdot_state_roads`, `fdot_county_roads`, `fdot_local_names`, `fdot_counties`, `fdot_cities`, `fdot_zip`, `fdacs_parcels`), `status` (`ok`, `error`, `timeout`), `ms`.

`MapSegment`:
- `start`, `end`: `MapPoint` de cada extremo.
- `road`: `RoadMatch` de la vía elegida, con `milepost` del inicio.
- `begin_milepost`, `end_milepost`, `length_mi`.
- `geometry`: GeoJSON `LineString` en WGS84 (`[[lon, lat], …]`) del tramo entre los dos mileposts.
- `osp_row`: `county`, `state_road_id`, `section_number`, `beginning_milepost`, `ending_milepost`, en el orden de la tabla Work Location de OSP.
- `jurisdiction`, `warnings`.

Avisos (`warnings`): `NO_ROAD_NEARBY`, `MULTIPLE_ROADS`, `SOURCE_FAILED`, `PARCEL_IS_ROAD`, `OUTSIDE_COUNTY_DATA`.

Errores nuevos (formato de `estilos/API.md`):
- 422 `COORDINATES_OUT_OF_FLORIDA`, `SEGMENT_ROADWAY_MISMATCH`, `SEGMENT_TOO_LONG`.
- 502 `GIS_UNAVAILABLE`: ninguna fuente respondió tras los reintentos.
- 503 `GIS_DISABLED`: `APP_GIS_ENABLED=false`.

## Diseño

- `services/gis/transport.py`: su propio `httpx.AsyncClient`, sin cabecera de autorización, con plazo `gis_timeout_seconds` (20), semáforo `gis_max_concurrency` (4) y `gis_max_retries` (2) ante 5xx o tiempo agotado. Nunca reutiliza el transporte de Smartsheet: el token no debe salir hacia terceros (ADR-B16).
- `services/gis/layers.py`: catálogo de capas (id de fuente, URL base configurable, campos). Las URL base salen de `gis_fdot_base_url` y `gis_fdacs_parcels_url` para poder apuntar al GIS falso en E2E.
- `services/gis/client.py`: `query_point(layer, lat, lon, fields, radius_m, with_m)`; traduce el error JSON de ArcGIS (`{"error": {...}}` con HTTP 200) a error de fuente.
- `services/gis/mappers.py` y `types.py`: JSON de ArcGIS a `RawRoad`, `RawBoundary`, `RawParcel`, `RawRoute` (con trayectos `[lon, lat, m]`).
- `services/map_rules.py`: puro: `in_florida`, `milepost_at`, `slice_route`, `pick_segment_road`, `jurisdiction` (tabla), `DOR_USES`, `normalize_route`. Si pasa de 300 líneas, separar `milepost.py`.
- `services/map.py`: `MapService.point` y `MapService.segment`; consultas en paralelo con `asyncio.TaskGroup` y caché `TtlCache`.
- `models/map.py` y `api/routes/map.py`: contrato y ruta delgada, con etiqueta propia en Swagger ("mapa").
- Configuración nueva en `core/config.py`: `app_gis_enabled` (true), `gis_fdot_base_url`, `gis_fdacs_parcels_url`, `gis_timeout_seconds`, `gis_max_concurrency`, `gis_max_retries`, `gis_cache_ttl_seconds`, `gis_max_segment_miles`.

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

## Fases

- M1: punto (CA-01 a CA-06, CA-08 a CA-11).
- M2: tramo (CA-07).
- M5: pendiente: adaptadores de condado con su propia fuente de jurisdicción, empezando por Palm Beach (`ENG/CENTERLINE`, campo `RESP_AUTH`); cada uno con su spec o una sección nueva aquí.

## Pendientes

- Turnpike en `osp_row` (GIS-PEN-01).
- Confirmar la tabla `DOR_UC` (MJ-PEN-05).
- Al implementar: `ARQUITECTURA.md`, `estilos/API.md`, `tecnologias/STACK.md` (sin dependencias nuevas previstas) y RESULTADOS.
