# GIS público de Florida: vía, milepost, calle, condado, ciudad, ZIP y parcela

Estado (2026-10-30): verificado con consultas reales sin sesión. Nada implementado. Reglas comunes WS-xx en `README.md`. Jurisdicción de calles, parcelas por condado y mapas base: `MAPAS_JURISDICCION_PARCELAS.md`.

## Conclusión

- GIS-C01: El milepost que OSP calcula en el paso 3 se obtiene igual desde los servicios GIS públicos del FDOT, sin iniciar sesión en OSP ni crear borradores (resuelve OSP-ENF-03).
- GIS-C02: Prueba con el tramo de `osp-milepost-paso3.png`: la SR 953 en Miami-Dade es la vía `87281000` (condado `87`, sección `281`, igual que el "Section Number 281" de OSP). Los mileposts 3.124 y 3.839 de OSP caen sobre "LEJEUNE RD/NW 42 AVE", del cruce con W Flagler St hacia el norte, y el cálculo inverso desde esos puntos devuelve 3.124 y 3.839 (a 0,0 m de la vía).
- GIS-C03: El ID de vía del FDOT tiene 8 dígitos: 2 de condado (numeración FDOT, 87 = Miami-Dade), 3 de sección y 3 de subsección. La "Section Number" de OSP son los 3 dígitos de la sección.
- GIS-C04: Los servicios del FDOT y de FDACS responden con `Access-Control-Allow-Origin` igual al origen que llama (probado con `http://localhost:5710`): una página web puede consultarlos directamente desde el navegador.

## Servicios del FDOT (`https://gis.fdot.gov/arcgis/rest/services`)

- GIS-F01: Directorio público con 46 servicios raíz y carpetas `Hosted`, `sso` y `Utilities`. Las carpetas `SoE_Services` y `Utilityviewer` piden token (error 499).
- GIS-F02: `RCI_Layers/MapServer` (30 capas mantenidas por la oficina TDA del FDOT). Las útiles aquí:
  - capa 8 "LRS Basemap Routes": líneas con medida M = milepost (`hasM: true`); campos `ROADWAY`, `COUNTY`, `SECTION`, `BEGIN_POST`, `END_POST`;
  - capa 13 "Roadways with Local Names": nombre local de la vía (`NAME`, por ejemplo "LEJEUNE RD/NW 42 AVE") con su rango de milepost;
  - capa 15 "State Roads": `ROADWAY`, `ROUTE` ("SR  953"), `ROUTENUM`, `COUNTY`, `DISTRICT`, `MNG_DIST`, `BEGIN_POST`, `END_POST`;
  - capa 27 "Mile Markers": postes de milla físicos (`MILEPOINT`);
  - otras: Toll Roads (24), Interstates (7), US Routes (20), Intersections (6), Traffic Signals (18) y más.
- GIS-F03: `Admin_Boundaries/MapServer`: capa 6 condados (`COUNTY`, `CNTYNO` FDOT, `FIPS`), capa 7 ciudades (`NAME`, `GEOID`), capa 8 códigos ZIP (`ZIP`, `PO_NAME`), capa 13 distritos FDOT con Turnpike, además de distritos legislativos.
- GIS-F04: `LrsDetective/GPServer/LrsDetective`: herramienta síncrona sin documentación. Parámetros `WhichFunction`, `Coordinates`, `SearchDistance`, `Roadway`, `Bmp`, `Emp`. Sólo se conoce la función por defecto `CreateLineFromRoadwayBmpEmp`: con vía y milepost inicial y final devuelve la línea del tramo (con M). Las demás funciones no se conocen; no adivinarlas a ciegas.
- GIS-F05: `FDOT_OSP_Permits/MapServer` y `newOSPlayer`: capas de permisos de OSP (líneas, puntos, banners, permisos de servicios públicos antiguos). Por revisar qué datos expone.
- GIS-F06: `Parcels`: pide token (error 499); usar GIS-P01.
- GIS-F07: Licencia: el FDOT publica sus datos "as is", sin garantía.

## Parcelas

- GIS-P01: FDACS, estatal: `https://gis.fdacs.gov/mapping/rest/services/GIO_Parcels_for_OAWP_Optimized/FeatureServer/0`. Público. Campos `CO_NO` (número de condado del DOR, 23 = Miami-Dade; no es la numeración FDOT), `PARCEL_ID`, `PARCELNO`, `DOR_UC` (uso de suelo DOR), `PA_UC`, `OWN_NAME`, entre otros. `maxRecordCount` 2000. Datos del Departamento de Ingresos (DOR) de Florida, que excluye registros confidenciales.
- GIS-P02: `OWN_NAME` es el nombre del propietario: dato personal. No guardarlo en docs, fixtures, logs ni capturas (WS-07); pedir sólo los campos necesarios con `outFields`.
- GIS-P03: Los servicios de los tasadores de cada condado pueden traer más detalle (dirección, valores); no revisados.

## Cómo calcular el milepost de un punto

- GIS-M01: Consultar la capa 8 de `RCI_Layers` con el punto en WGS84 (`inSR=4326`), un radio de unos 25 m (`distance=25&units=esriSRUnit_Meter`), `returnGeometry=true`, `returnM=true` y `outSR=4326`.
- GIS-M02: Proyectar el punto sobre la línea devuelta e interpolar la M del segmento más cercano: ese valor es el milepost. En un cruce aparecen varias vías; elegir la más cercana o la del tipo buscado (por ejemplo, la que también está en "State Roads").
- GIS-M03: Para un tramo dibujado, aplicar GIS-M01 y GIS-M02 al punto inicial y al final: salen el Beginning Milepost y el Ending Milepost.
- GIS-M04: Con la misma consulta de punto en las capas 13 y 15 de `RCI_Layers` y 6, 7 y 8 de `Admin_Boundaries` salen el nombre de la calle, la ruta estatal, el condado, la ciudad y el ZIP.
- GIS-M05: El script de prueba usado no se guardó en el repositorio; se reescribe al implementar.

## Calles y mapa base

- GIS-B01: La capa 13 sólo nombra las vías que están en el sistema de referencia del FDOT (estatales y algunas locales), no todas las calles.
- GIS-B02: Para ver todas las calles basta un mapa base con nombres (por ejemplo, teselas de OpenStreetMap con su atribución y su política de uso). Para buscar calles o direcciones por texto: geocodificadores públicos como el del Censo de EE. UU. u OpenStreetMap Nominatim; no verificados aquí.
- GIS-B03: TIGERweb del Censo (`tigerweb.geo.census.gov`) no devolvió JSON en la prueba; no verificado.

## Pendientes (GIS-PEN)

- GIS-PEN-01: Confirmar cómo decide OSP "Is Location on Turnpike?" (candidatos: capa 13 de `Admin_Boundaries`, `MNG_DIST` de la vía o la capa Toll Roads). Avance 2026-10-30: la capa 13 ("Detailed FDOT District Bndy_w_TPIKE", campo `DVALUE`) da `D8` / `FTE` sobre SR 821 y sólo `D6` sobre SR 953; el panel la usa (SPEC-B14 punto 10). Falta compararlo con OSP en un tramo del Turnpike.
- GIS-PEN-02: Probar más tramos, incluidas vías locales y cruces, y comparar con OSP.
- GIS-PEN-03: Revisar qué expone `FDOT_OSP_Permits` (GIS-F05).
- GIS-PEN-04: Elegir el mapa base y revisar sus condiciones de uso antes de un uso continuo.
