import 'leaflet/dist/leaflet.css'
import { useEffect, useRef, useState } from 'react'
import type { Coordinates } from '../../features/map/lib/coordinates'
import { basemaps, fdotRoads, maxZoom, type Basemap } from './tileSources'

export type MapMarker = Coordinates & { label?: string }
/** Pedido de mover la vista: sólo al buscar o al abrir una URL; un clic no mueve el mapa. */
export type MapFocus = Coordinates & { zoom: number }
export type { Basemap }

type Props = {
  focus: MapFocus | null
  markers: MapMarker[]
  line: [number, number][]
  basemap: Basemap
  /** Capa opcional con las vías estatales y de condado del FDOT. */
  roads: boolean
  onMapClick: (point: Coordinates) => void
}
const start: MapFocus = { lat: 26.1, lon: -80.25, zoom: 10 }

export function MapView({ focus, markers, line, basemap, roads, onMapClick }: Props) {
  const element = useRef<HTMLDivElement>(null)
  // Leaflet se importa una sola vez y los demás efectos esperan a `ready`: con una importación
  // por efecto, el orden en que se resuelven no está garantizado y un marcador podía perderse.
  const leaflet = useRef<typeof import('leaflet') | null>(null)
  const map = useRef<import('leaflet').Map | null>(null)
  const layers = useRef<import('leaflet').LayerGroup | null>(null)
  const tile = useRef<import('leaflet').TileLayer | null>(null)
  const [ready, setReady] = useState(false)
  const click = useRef(onMapClick)
  useEffect(() => {
    click.current = onMapClick
  }, [onMapClick])
  useEffect(() => {
    let active = true
    void import('leaflet').then((L) => {
      if (!active || !element.current) return
      const view = focus ?? start
      const instance = L.map(element.current, { zoomControl: true, maxZoom }).setView(
        [view.lat, view.lon],
        view.zoom,
      )
      L.control.scale({ imperial: true, metric: true }).addTo(instance)
      leaflet.current = L
      map.current = instance
      layers.current = L.layerGroup().addTo(instance)
      instance.on('click', (event) => click.current({ lat: event.latlng.lat, lon: event.latlng.lng }))
      setReady(true)
    })
    return () => {
      active = false
      map.current?.remove()
      map.current = null
      layers.current = null
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
    const L = leaflet.current
    const group = layers.current
    if (!ready || !L || !group) return
    group.clearLayers()
    if (line.length > 1)
      L.polyline(
        line.map(([lon, lat]) => [lat, lon]),
        { className: 'map-line', weight: 6 },
      ).addTo(group)
    markers.forEach((item) => {
      const marker = L.circleMarker([item.lat, item.lon], { radius: 8, className: 'map-marker' })
      if (item.label) marker.bindTooltip(item.label, { permanent: true, direction: 'top', offset: [0, -8] })
      marker.addTo(group)
    })
  }, [ready, line, markers])
  useEffect(() => {
    if (ready && focus) map.current?.setView([focus.lat, focus.lon], focus.zoom)
  }, [ready, focus])
  return <div ref={element} className="map-view" role="application" aria-label="Mapa" />
}
