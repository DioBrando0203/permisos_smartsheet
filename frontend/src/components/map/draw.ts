import type { Coordinates } from '../../features/map/lib/coordinates'

type Leaflet = typeof import('leaflet')
type Group = import('leaflet').LayerGroup

export type MapMarker = Coordinates & { label?: string; small?: boolean }
/** Línea [[lon, lat], …]: `draft` es un trazo a medias; `result`, lo que respondió el backend. */
export type MapLine = { coordinates: [number, number][]; style: 'draft' | 'result' }
/** Línea de una capa temática (calles por responsable): clase de color y texto al pasar. */
export type MapOverlay = {
  coordinates: [number, number][]
  className: string
  weight?: number
  tooltip?: string
}

/** Panel de Leaflet de las capas temáticas: debajo de los resultados (overlayPane es 400). */
export const overlayPane = 'overlays'

export const toLatLng = (line: [number, number][]) => line.map(([lon, lat]) => [lat, lon] as [number, number])

/**
 * Resultados y marcadores: todo se redibuja en cada cambio y sin clic propio
 * (`interactive: false`): si el segundo clic de un doble clic cayera sobre un marcador recién
 * borrado, el mapa no recibiría el doble clic y el trazo no terminaría.
 */
export function drawResults(L: Leaflet, group: Group, lines: MapLine[], markers: MapMarker[]) {
  group.clearLayers()
  lines
    .filter((line) => line.coordinates.length > 1)
    .forEach((line) => {
      L.polyline(toLatLng(line.coordinates), {
        className: `map-line map-line--${line.style}`,
        weight: line.style === 'draft' ? 3 : 6,
        interactive: false,
      }).addTo(group)
    })
  markers.forEach((item) => {
    const marker = L.circleMarker([item.lat, item.lon], {
      radius: item.small ? 5 : 8,
      className: 'map-marker',
      interactive: false,
    })
    if (item.label) marker.bindTooltip(item.label, { permanent: true, direction: 'top', offset: [0, -8] })
    marker.addTo(group)
  })
}

/**
 * Capa temática con texto al pasar el cursor. Las líneas reciben el ratón para el texto, pero
 * el clic y el doble clic siguen llegando al mapa (`bubblingMouseEvents`): consultar el punto o
 * terminar el trazo funciona igual encima de una calle.
 */
export function drawOverlays(L: Leaflet, group: Group, overlays: MapOverlay[]) {
  group.clearLayers()
  overlays
    .filter((overlay) => overlay.coordinates.length > 1)
    .forEach((overlay) => {
      const line = L.polyline(toLatLng(overlay.coordinates), {
        className: overlay.className,
        weight: overlay.weight ?? 4,
        pane: overlayPane,
        bubblingMouseEvents: true,
      })
      if (overlay.tooltip) line.bindTooltip(overlay.tooltip, { sticky: true, direction: 'top' })
      line.addTo(group)
    })
}
