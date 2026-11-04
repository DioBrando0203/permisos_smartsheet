# Mapas gratuitos, dueños de calles y parcelas (Broward, Palm Beach, Martin, Miami-Dade, St. Johns)

Estado (2026-10-30): investigación con consultas reales sin sesión; parte verificada y parte pendiente, marcada en cada punto. La fase 1, los respaldos de parcelas y el adaptador de St. Johns (2026-11-03, PEN-40) ya están en el panel (SPEC-B14); el resto está sin implementar. Reglas comunes WS-xx en `README.md`; servicios del FDOT y cálculo de milepost en `GIS_PUBLICO_FLORIDA.md`.

## Respuesta corta

- MJ-R01: No hay una sola fuente que lo dé todo. La mejor base única para empezar es estatal y gratuita: FDOT para vías, milepost, ciudad, condado y ZIP, y FDACS para parcelas. Cubre todos los condados con el mismo formato.
- MJ-R02: El detalle fino (quién responde por cada calle local, dirección y valores del predio, ventas) está en los servicios de cada condado, con formatos y calidad distintos. Se agrega después, condado por condado.
- MJ-R03: Todos los condados del sur de Florida están en el Distrito 4 del FDOT, salvo Miami-Dade (Distrito 6). St. Johns está en el Distrito 2 (código FDOT 78, DOR 65).

## Fase 1: lo básico, una sola base estatal (recomendada para empezar)

- MJ-F1-01: Un clic o un tramo en el mapa devuelve: vía y su tipo (estatal, de condado u otra), milepost, nombre de la calle, ciudad o "zona no incorporada", condado, ZIP y parcela (ID y código de uso del DOR).
- MJ-F1-02: Regla aproximada de jurisdicción de la calle:
  - si la vía está en "State Roads" (capa 15 de `RCI_Layers`), es del Estado (FDOT) y el permiso va por OSP;
  - si está en "County Roads" (capa 2), es de condado (CR);
  - si es otra vía dentro de una ciudad, probablemente es de la ciudad; fuera de toda ciudad, probablemente del condado;
  - es una aproximación: también hay calles privadas y de distritos especiales (ver MJ-PB-02), y en Broward la capa 2 no tiene vías (MJ-BR-03).
- MJ-F1-03: Pruebas hechas el 2026-10-30, una vía estatal y una de condado por condado, tomadas de las propias capas:
  - Broward: I-75 (vía `86075000`, SR 93), milepost 11.650, ciudad Sunrise; capa de condado vacía para Broward;
  - Palm Beach: SR 809 Military Trail (`93150000`), milepost 8.879, Palm Beach Gardens; CR 811 (`93000162`), milepost 0.308, Riviera Beach;
  - Martin: SR A1A NE Ocean Blvd (`89040000`), milepost 8.492, zona no incorporada; CR A1A SE 5 St (`89000115`), milepost 0.074, Stuart;
  - Fort Lauderdale: W Las Olas Blvd (`86000142`) y SE 4 St (`86000660`) salen como vías locales, ni estatales ni de condado.
- MJ-F1-04: La capa HPMS (capa 4, campo `ON_OFF_SYS`) no aportó nada al cruzarla por `ROADWAY`; descartada para esto.

## Parcelas estatales (FDACS)

- MJ-PE-01: Servicio `https://gis.fdacs.gov/mapping/rest/services/GIO_Parcels_for_OAWP_Optimized/FeatureServer/0`: público, con CORS, más de 10 millones de parcelas; datos del DOR que entregan los 67 tasadores de condado y se actualizan una vez al año.
- MJ-PE-02: La numeración de condados del DOR (`CO_NO`) no es la del FDOT. Observado en las pruebas: Broward 16, Miami-Dade 23, Martin 53, Palm Beach 60. En el FDOT: Broward 86, Miami-Dade 87, Martin 89, Palm Beach 93.
- MJ-PE-03: El formato de `PARCEL_ID` cambia por condado: 12 dígitos en Broward, 17 en Palm Beach, con guiones en Martin.
- MJ-PE-04: `DOR_UC` (uso de suelo) sirve para saber si un predio es público: 086 condado, 087 estado, 088 federal, 089 municipal, 094 derecho de vía (calles y caminos). Valores según la tabla de usos del DOR, por confirmar con la fuente oficial (MJ-PEN-05). En las pruebas, la I-75 cayó sobre una parcela 094 y un predio de Stuart sobre una 089.
- MJ-PE-05: Algunas vías aparecen como polígono sin ID (`CO_NO` 0, `PARCEL_ID` vacío), como en Las Olas.
- MJ-PE-06: `OWN_NAME` es el nombre del propietario. En Florida es registro público, pero aquí se trata como dato personal (WS-07): se puede mostrar en la app si hace falta, nunca guardarlo en docs, fixtures ni logs. Los propietarios que son entidades públicas no tienen ese problema.

## Fase 2: detalle por condado

Palm Beach (verificado el 2026-10-30, `https://gis.pbcgov.org/arcgis/rest/services`):
- MJ-PB-01: `ENG/CENTERLINE/MapServer/0`: eje de todas las calles del condado con nombre, rangos de direcciones, ZIP, municipio a cada lado (`L_MUNI`, `R_MUNI`), clase funcional, carriles, velocidad, `COUNTY_RD_ID` y `TFARE_ROW` (derecho de vía).
- MJ-PB-02: El campo `RESP_AUTH` dice quién responde por cada calle: `FDOT`, `COUNTY`, `MUN` (municipio), `PRI` (privada), `ITID` (Indian Trail Improvement District), `SIRWCD` (South Indian River Water Control District) o vacío. `MAINTBY` y `OWNEDBY` existen pero están vacíos.
- MJ-PB-03: Otros servicios públicos de ingeniería: `ENG/RIGHT_OF_WAY`, `ENG/MAJOR_RD`, `ENG/UNNAMED_ROADS` y `ENG/EPERMITS` / `ENG/EPERMIT_DATA` (permisos de ingeniería del condado; por revisar, MJ-PEN-04). La carpeta `TELECOM` pide token.
- MJ-PB-04: Carpeta `Parcels`, del tasador (PAPA/PAO): `PAO_PARCELS_WM`, `PARCELS`, `PARCEL_INFO` (capa 4 `PARCEL_DETAILS`), `PARCEL_PROPERTY_USE_PAPA`, `PARCEL_SALES_PAPA`, `QSALES`, `HOMESTEAD`. Campos no revisados.

Broward (parcial):
- MJ-BR-01: `https://services.arcgis.com/JMAJrTsHNLrSsWf5/ArcGIS/rest/services/Parcels/FeatureServer/0`: geometría de parcelas con `FOLIO` y `PARCEL_TYP`, sin datos del tasador.
- MJ-BR-02: `…/RealPropertyFilter/FeatureServer/0` ("Real Property Query"): datos del tasador (BCPA): folio, uso, propietario, dirección, valores, venta y exenciones. Su descripción dice que lo pidió la administración del condado para un tablero de propiedades; puede no cubrir todas las parcelas (MJ-PEN-01).
- MJ-BR-03: Jurisdicción de calles en Broward: sin fuente encontrada; la capa de vías de condado del FDOT está vacía para Broward (MJ-PEN-01).

Martin (sin fuente propia confirmada):
- MJ-MA-01: El tasador (`pa.martin.fl.us`) tiene un buscador GIS, pero no se encontró un servicio REST público. Por ahora usar FDACS (`CO_NO` 53) y el FDOT (MJ-PEN-02).

Miami-Dade:
- MJ-MD-01: No investigado en esta ronda (MJ-PEN-03).

St. Johns (verificado el 2026-11-03 con GET sin sesión; implementado en PEN-40):
- MJ-SJ-01: Directorio público `https://www.gis.sjcfl.us/sjcgis/rest/services` (ArcGIS 11.5, sin token). Responde JSON con `Access-Control-Allow-Origin` igual al origen (probado con `http://localhost:5710`) y tarda unos 0,4 s por consulta de punto.
- MJ-SJ-02: `Road/MapServer/36` (escala 1:600 a 1:4800, la más detallada): eje de todas las calles del condado con `NAME`, rangos de direcciones, `CITYLFT`/`CITYRGT` (`St Augustine`, `St Augustine Beach`, `Unincorporated`), `GATED` (`Y`/`N`), `CLASS` y `MAINTENANCE`. `maxRecordCount` 1000. Las capas 4, 11, 19 y 27 son el mismo dato a escalas menores.
- MJ-SJ-03: `MAINTENANCE` dice quién mantiene cada tramo. Conteo de tramos: `St Johns County` 8344, `Private` 6013, `City of St Augustine` 1202, `State of Florida` 922, `Proposed` 483, `Private CDD` 400, `City of St Augustine Beach` 284, `Out of County` 128, `Emergency Access` 19, vacío 11, `Parks and Recreation` 9.
- MJ-SJ-04: Casos de prueba con el radio de 25 m: King St y Cordova St en St. Augustine dan `City of St Augustine` (el FDOT las tiene como vías locales); 8th St en St. Augustine Beach da `City of St Augustine Beach` (el FDOT no tiene vía); Tidestone Dr (30.010961, -81.516193) da `St Johns County`; UF Health Way (30.088861, -81.515803) da `Private`; Greyson Ct (30.015785, -81.568375) da `Private CDD`; State Road 9B (30.094993, -81.518816) da `State of Florida`.
- MJ-SJ-05: Hastings sigue como municipio en el Censo (capa 7 de `Admin_Boundaries`, `CLASSFP` C1), pero el condado marca sus calles (N First St, E Cochran Ave) como `St Johns County` y la zona como `Unincorporated`; `MAINTENANCE` no tiene ningún valor de Hastings.
- MJ-SJ-06: `State of Florida` aparece también en tramos cortos de calles de condado (por ejemplo, 6 de los 29 tramos de International Golf Pkwy, Double Gate Rd y Kling Rd), probablemente los accesos a un cruce con una vía estatal. Por eso el panel sólo da confianza alta a "estatal" si el FDOT también ve una vía estatal en el radio.
- MJ-SJ-07: Los ejes del condado y la LRS del FDOT no coinciden al metro: en Nocatee (30.105, -81.42) el FDOT da la vía `78000805` a 22 m y el condado no tiene calle a 25 m (sí a 80 m: Marietta Dr, `Private`, y Preservation Trl, `St Johns County`).
- MJ-SJ-08: Parcelas: `Parcel/MapServer/0` con `PIN` ("199570 0000"), `STRAP` ("1995700000", igual al `PARCEL_ID` de FDACS), `USE_CODE` ("8900"), `USE_DESC` ("Municipally Owned") y datos del propietario (dato personal, WS-07). FDACS responde en St. Johns, así que no se usa por ahora.
- MJ-SJ-09: Otros servicios del condado: `Transportation` (conteos de tráfico), `iMap_Dynamic` (zonificación, distritos, ZIP, proyectos de ingeniería) y `Road_Survey`. No revisados.
- MJ-SJ-10: Lugares censales: Nocatee y World Golf Village tienen `CLASSFP` U2 en la capa 7 de `Admin_Boundaries`; St. Augustine y St. Augustine Beach, C1. En Florida la capa 7 tiene 410 C1, 425 U1, 80 U2, 4 M2 (bases militares) y 1 C9 (Islandia, inactivo); Jacksonville también es C1.
- MJ-SJ-11: Tipo de municipio (`LSAD` de la capa 7, verificado el 2026-11-03): 25 city (267), 43 town (124) y 47 village (19). Ejemplos: Miami y St. Augustine city; Jupiter, Davie y Palm Beach town; Wellington, Royal Palm Beach, Key Biscayne y Pinecrest village. Indiantown (Martin) se incorporó como village, pero el Censo todavía la tiene como CDP (`U1`, `LSAD` 57): el panel la muestra como zona no incorporada hasta que haya un adaptador de Martin.

Ciudades:
- MJ-CI-01: Algunas ciudades publican sus propios servicios, por ejemplo West Palm Beach (`wpbgisportal.wpb.org`, `Parcel/Parcels_New`, copia mensual de los datos del condado). No revisados.

## Mapas base gratuitos

- MJ-B01: USGS The National Map (`basemap.nationalmap.gov`: `USGSTopo`, `USGSImageryOnly`, `USGSImageryTopo` y otros): dominio público, gratis incluso para uso comercial y sin cuenta. Es de estilo topográfico, con menos detalle de calles que un mapa urbano. Fuente: preguntas frecuentes de USGS sobre términos de uso.
- MJ-B02: Esri (ArcGIS Location Platform): plan gratis de 2.000.000 de teselas al mes, o 1.000 sesiones al mes en el modelo por sesión. Requiere cuenta y clave de API. Si se activa el pago por uso no hay tope automático, hay que vigilar el consumo. Fuente: `https://location.arcgis.com/pricing/`; las cifras pueden cambiar.
- MJ-B03: OpenStreetMap (`tile.openstreetmap.org`): los datos son libres, pero sus servidores de teselas no son para apps comerciales en producción; el uso intenso está prohibido sin permiso y pueden bloquear sin aviso. Sirve para pruebas locales con atribución. Para producción, un proveedor de teselas basado en OSM o servirlas uno mismo. Fuente: `https://operations.osmfoundation.org/policies/tiles/`.
- MJ-B04: Recomendación: prototipo local con OSM o USGS. Para producción, Esri con el plan gratis y la clave restringida al dominio de la app, o USGS si el costo tiene que ser cero sin excepción.

## Pendientes (MJ-PEN)

- MJ-PEN-01: Broward: encontrar una fuente de jurisdicción de calles (condado o ciudad) y confirmar si MJ-BR-02 cubre todas las parcelas.
- MJ-PEN-02: Martin: buscar un servicio REST del tasador o un eje de calles del condado con jurisdicción.
- MJ-PEN-03: Miami-Dade: parcelas y jurisdicción de calles.
- MJ-PEN-04: Palm Beach: revisar `ENG/EPERMITS`, `ENG/RIGHT_OF_WAY` y los campos de `Parcels/PARCEL_INFO`.
- MJ-PEN-05: Confirmar los códigos `DOR_UC` con la tabla oficial del DOR.
- MJ-PEN-06: Revisar las condiciones de uso de cada servicio de condado antes de un uso continuo (incluye St. Johns, MJ-SJ-01).
- MJ-PEN-07: Ciudades de Broward con servicios propios.
