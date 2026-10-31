import 'leaflet/dist/leaflet.css'
import { useEffect, useRef, useState } from 'react'
import type { Coordinates } from '../../features/map/lib/coordinates'
import { basemaps, fdotRoads, maxZoom, type Basemap } from './tileSources'

export type MapMarker = Coordinates & { label?: string; small?: boolean }
export type MapBounds = { west: number; south: number; east: number; north: number }
/** Pedido de mover la vista: al buscar, al elegir una zona o al abrir una URL; un clic no la mueve. */
export type MapFocus = (Coordinates & { zoom: number }) | { bounds: MapBounds }
/** Línea [[lon, lat], …]: `draft` es un trazo a medias; `result`, lo que respondió el backend. */
export type MapLine = { coordinates: [number, number][]; style: 'draft' | 'result' }
export type MapViewState = { bounds: MapBounds; zoom: number }
export type { Basemap }

type Props = {
  focus: MapFocus | null
  markers: MapMarker[]
  lines: MapLine[]
  /** Contornos [[lon, lat], …] finos y sin clic, debajo de todo lo demás. */
  outlines: [number, number][][]
  /** Contorno punteado de la zona elegida (condado o ciudad), sin clic. */
  area: [number, number][][]
  basemap: Basemap
  /** Capa opcional con las vías estatales y de condado del FDOT. */
  roads: boolean
  /** Mientras se dibuja, el doble clic termina el trazo en vez de acercar. */
  drawing: boolean
  onMapClick: (point: Coordinates) => void
  onMapDoubleClick: (point: Coordinates) => void
  onViewChange: (view: MapViewState) => void
}
type Handlers = Pick<Props, 'onMapClick' | 'onMapDoubleClick' | 'onViewChange'>
const start = { lat: 26.1, lon: -80.25, zoom: 10 }
const toLatLng = (line: [number, number][]) => line.map(([lon, lat]) => [lat, lon] as [number, number])

export function MapView(props: Props) {
  const { focus, markers, lines, outlines, area, basemap, roads, drawing } = props
  const element = useRef<HTMLDivElement>(null)
  // Leaflet se importa una sola vez y los demás efectos esperan a `ready`: con una importación
  // por efecto, el orden en que se resuelven no está garantizado y un marcador podía perderse.
  const leaflet = useRef<typeof import('leaflet') | null>(null)
  const map = useRef<import('leaflet').Map | null>(null)
  const layers = useRef<import('leaflet').LayerGroup | null>(null)
  const outlineLayer = useRef<import('leaflet').LayerGroup | null>(null)
  const areaLayer = useRef<import('leaflet').LayerGroup | null>(null)
  const tile = useRef<import('leaflet').TileLayer | null>(null)
  const [ready, setReady] = useState(false)
  const handlers = useRef<Handlers>(props)
  useEffect(() => {
    handlers.current = props
  })
  useEffect(() => {
    let active = true
    void import('leaflet').then((L) => {
      if (!active || !element.current) return
      // Un rectángulo (zona) se encuadra en el efecto de `focus`, cuando el mapa ya existe.
      const view = focus && 'lat' in focus ? focus : start
      const instance = L.map(element.current, { zoomControl: true, maxZoom }).setView(
        [view.lat, view.lon],
        view.zoom,
      )
      L.control.scale({ imperial: true, metric: true }).addTo(instance)
      leaflet.current = L
      map.current = instance
      areaLayer.current = L.layerGroup().addTo(instance)
      outlineLayer.current = L.layerGroup().addTo(instance)
      layers.current = L.layerGroup().addTo(instance)
      const at = (event: import('leaflet').LeafletMouseEvent) => ({
        lat: event.latlng.lat,
        lon: event.latlng.lng,
      })
      instance.on('click', (event) => handlers.current.onMapClick(at(event)))
      instance.on('dblclick', (event) => handlers.current.onMapDoubleClick(at(event)))
      const report = () => {
        const bounds = instance.getBounds()
        handlers.current.onViewChange({
          bounds: {
            west: bounds.getWest(),
            south: bounds.getSouth(),
            east: bounds.getEast(),
            north: bounds.getNorth(),
          },
          zoom: instance.getZoom(),
        })
      }
      instance.on('moveend', report)
      report()
      setReady(true)
    })
    return () => {
      active = false
      map.current?.remove()
      map.current = null
      layers.current = null
      outlineLayer.current = null
      areaLayer.current = null
      tile.current = null
      setReady(false)
    }
    // El mapa se crea una sola vez; los cambios de vista llegan por `focus`.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])
  useEffect(() => {
    const L = leaflet.current
    if (!ready || !L || !map.current) return
    tile.current?.remove()
    const { url, ...options } = basemaps[basemap]
    tile.current = L.tileLayer(url, { ...options, maxZoom }).addTo(map.current)
  }, [ready, basemap])
  useEffect(() => {
    const L = leaflet.current
    if (!ready || !L || !map.current || !roads) return
    const { url, ...options } = fdotRoads
    const overlay = L.tileLayer(url, { ...options, maxZoom, zIndex: 2 }).addTo(map.current)
    return () => {
      overlay.remove()
    }
  }, [ready, roads])
  useEffect(() => {
    if (!ready || !map.current) return
    if (drawing) map.current.doubleClickZoom.disable()
    else map.current.doubleClickZoom.enable()
  }, [ready, drawing])
  useEffect(() => {
    const L = leaflet.current
    const group = outlineLayer.current
    if (!ready || !L || !group) return
    group.clearLayers()
    if (outlines.length)
      L.polyline(outlines.map(toLatLng), { className: 'map-parcel', weight: 1, interactive: false }).addTo(
        group,
      )
  }, [ready, outlines])
  useEffect(() => {
    const L = leaflet.current
    const group = layers.current
    if (!ready || !L || !group) return
    // Todo se redibuja en cada cambio y sin clic propio (`interactive: false`): si el segundo
    // clic de un doble clic cayera sobre un marcador recién borrado, el mapa no recibiría el
    // doble clic y el trazo no terminaría.
    group.clearLayers()
    lines
      .filter((line) => line.coordinates.length > 1)
      .forEach((line) => {
        const weight = line.style === 'draft' ? 3 : 6
        L.polyline(toLatLng(line.coordinates), {
          className: `map-line map-line--${line.style}`,
          weight,
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
  }, [ready, lines, markers])
  useEffect(() => {
    const L = leaflet.current
    const group = areaLayer.current
    if (!ready || !L || !group) return
    group.clearLayers()
    if (area.length)
      L.polyline(area.map(toLatLng), { className: 'map-area', weight: 2, interactive: false }).addTo(group)
  }, [ready, area])
  useEffect(() => {
    if (!ready || !focus || !map.current) return
    if ('bounds' in focus) {
      const { west, south, east, north } = focus.bounds
      map.current.fitBounds(
        [
          [south, west],
          [north, east],
        ],
        { padding: [16, 16] },
      )
    } else map.current.setView([focus.lat, focus.lon], focus.zoom)
  }, [ready, focus])
  return <div ref={element} className="map-view" role="application" aria-label="Mapa" />
}
