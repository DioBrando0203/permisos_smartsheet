import 'leaflet/dist/leaflet.css'
import { useEffect, useRef } from 'react'
import type { Coordinates } from '../../features/map/lib/coordinates'

export type MapMarker = Coordinates & { label?: string }
/** Pedido de mover la vista: sólo al buscar o al abrir una URL; un clic no mueve el mapa. */
export type MapFocus = Coordinates & { zoom: number }

type Props = {
  focus: MapFocus | null
  markers: MapMarker[]
  line: [number, number][]
  basemap: 'streets' | 'satellite'
  onMapClick: (point: Coordinates) => void
}
const tiles = {
  streets: 'https://basemap.nationalmap.gov/arcgis/rest/services/USGSTopo/MapServer/tile/{z}/{y}/{x}',
  satellite:
    'https://basemap.nationalmap.gov/arcgis/rest/services/USGSImageryTopo/MapServer/tile/{z}/{y}/{x}',
}
const start: MapFocus = { lat: 26.1, lon: -80.25, zoom: 10 }

export function MapView({ focus, markers, line, basemap, onMapClick }: Props) {
  const element = useRef<HTMLDivElement>(null)
  const map = useRef<import('leaflet').Map | null>(null)
  const layers = useRef<import('leaflet').LayerGroup | null>(null)
  const tile = useRef<import('leaflet').TileLayer | null>(null)
  const click = useRef(onMapClick)
  useEffect(() => {
    click.current = onMapClick
  }, [onMapClick])
  useEffect(() => {
    let active = true
    void import('leaflet').then((L) => {
      if (!active || !element.current) return
      const view = focus ?? start
      const instance = L.map(element.current, { zoomControl: true }).setView([view.lat, view.lon], view.zoom)
      map.current = instance
      layers.current = L.layerGroup().addTo(instance)
      instance.on('click', (event) => click.current({ lat: event.latlng.lat, lon: event.latlng.lng }))
    })
    return () => {
      active = false
      map.current?.remove()
      map.current = null
      tile.current = null
    }
    // El mapa se crea una sola vez; los cambios de vista llegan por `focus`.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])
  useEffect(() => {
    void import('leaflet').then((L) => {
      if (!map.current) return
      tile.current?.remove()
      tile.current = L.tileLayer(tiles[basemap], {
        maxNativeZoom: 16,
        maxZoom: 19,
        attribution: 'USGS The National Map',
      }).addTo(map.current)
    })
  }, [basemap])
  useEffect(() => {
    void import('leaflet').then((L) => {
      if (!layers.current) return
      layers.current.clearLayers()
      if (line.length > 1)
        L.polyline(
          line.map(([lon, lat]) => [lat, lon]),
          { className: 'map-line', weight: 6 },
        ).addTo(layers.current)
      markers.forEach((item) => {
        const marker = L.circleMarker([item.lat, item.lon], { radius: 8, className: 'map-marker' })
        if (item.label) marker.bindTooltip(item.label, { permanent: true, direction: 'top', offset: [0, -8] })
        marker.addTo(layers.current!)
      })
    })
  }, [line, markers])
  useEffect(() => {
    if (!focus) return
    void import('leaflet').then(() => map.current?.setView([focus.lat, focus.lon], focus.zoom))
  }, [focus])
  return <div ref={element} className="map-view" role="application" aria-label="Mapa" />
}
