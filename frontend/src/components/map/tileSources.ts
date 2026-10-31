/**
 * Imágenes que el navegador pide directo a servicios públicos sin clave (excepción de ADR-13).
 * USGS NAIP y FDOT no tienen teselas fijas: dibujan una imagen por área, y Leaflet arma esa
 * área (`{bbox}`) con la función del mismo nombre en las opciones de la capa.
 */
export const basemapChoices = ['streets', 'satellite', 'hd'] as const
export type Basemap = (typeof basemapChoices)[number]
type TileSource = { url: string; attribution: string; maxNativeZoom?: number; bbox?: typeof tileBbox }

export const maxZoom = 20
// Medio ancho del mundo en Web Mercator (EPSG:3857), en metros.
const world = 20037508.342789244

/** Área de la tesela x, y, z en EPSG:3857, como la piden los `export` de ArcGIS. */
export function tileBbox({ x, y, z }: { x: number; y: number; z: number }): string {
  const size = (2 * world) / 2 ** z
  const bounds = [-world + x * size, world - (y + 1) * size, -world + (x + 1) * size, world - y * size]
  return bounds.map((value) => value.toFixed(2)).join(',')
}

const exportArea = 'bboxSR=3857&imageSR=3857&size=256,256&f=image&bbox={bbox}'
const usgsTiles = (service: string) =>
  `https://basemap.nationalmap.gov/arcgis/rest/services/${service}/MapServer/tile/{z}/{y}/{x}`

export const basemaps: Record<Basemap, TileSource> = {
  // Teselas fijas de USGS: en el sur de Florida sólo llegan al zoom 16 (más cerca se amplían).
  streets: { url: usgsTiles('USGSTopo'), attribution: 'USGS The National Map', maxNativeZoom: 16 },
  satellite: { url: usgsTiles('USGSImageryTopo'), attribution: 'USGS The National Map', maxNativeZoom: 16 },
  // Ortofoto NAIP (píxel de 30 cm, dominio público): nítida hasta el zoom 19-20, algo más lenta.
  hd: {
    url: `https://imagery.nationalmap.gov/arcgis/rest/services/USGSNAIPPlus/ImageServer/exportImage?format=jpg&${exportArea}`,
    attribution: 'USGS NAIP Plus',
    bbox: tileBbox,
  },
}

// Colores de --map-road-state y --map-road-county (tokens.css), en RGBA para ArcGIS.
const roadStyle = (layer: number, color: number[], width: number) => ({
  id: layer,
  source: { type: 'mapLayer', mapLayerId: layer },
  drawingInfo: {
    renderer: { type: 'simple', symbol: { type: 'esriSLS', style: 'esriSLSSolid', color, width } },
  },
})
const roadLayers = [roadStyle(2, [14, 138, 70, 230], 3), roadStyle(15, [230, 110, 0, 230], 4)]

/** Vías de condado (capa 2) y estatales (capa 15) del FDOT, sobre cualquier mapa base. */
export const fdotRoads: TileSource = {
  url: `https://gis.fdot.gov/arcgis/rest/services/RCI_Layers/MapServer/export?format=png32&transparent=true&dynamicLayers=${encodeURIComponent(JSON.stringify(roadLayers))}&${exportArea}`,
  attribution: 'FDOT',
  bbox: tileBbox,
}
