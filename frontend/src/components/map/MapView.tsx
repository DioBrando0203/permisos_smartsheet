import 'leaflet/dist/leaflet.css'
import { useEffect, useRef } from 'react'
import type { Coordinates } from '../../features/map/lib/coordinates'

type Props = {
  center: Coordinates
  zoom: number
  markers: Coordinates[]
  line: [number, number][]
  basemap: 'streets' | 'satellite'
  onMapClick: (point: Coordinates) => void
  onViewChange?: (point: Coordinates, zoom: number) => void
}
const tiles = {
  streets: 'https://basemap.nationalmap.gov/arcgis/rest/services/USGSTopo/MapServer/tile/{z}/{y}/{x}',
  satellite:
    'https://basemap.nationalmap.gov/arcgis/rest/services/USGSImageryTopo/MapServer/tile/{z}/{y}/{x}',
}

export function MapView({ center, zoom, markers, line, basemap, onMapClick, onViewChange }: Props) {
  const element = useRef<HTMLDivElement>(null)
  const map = useRef<import('leaflet').Map | null>(null)
  const layers = useRef<import('leaflet').LayerGroup | null>(null)
  const tile = useRef<import('leaflet').TileLayer | null>(null)
  const click = useRef(onMapClick)
  const viewChange = useRef(onViewChange)
  useEffect(() => {
    click.current = onMapClick
  }, [onMapClick])
  useEffect(() => {
    viewChange.current = onViewChange
  }, [onViewChange])
  useEffect(() => {
    let active = true
    void import('leaflet').then((L) => {
      if (!active || !element.current) return
      const instance = L.map(element.current, { zoomControl: true }).setView([26.1, -80.25], 10)
      map.current = instance
      layers.current = L.layerGroup().addTo(instance)
      instance.on('click', (event) => click.current({ lat: event.latlng.lat, lon: event.latlng.lng }))
      instance.on('moveend', () => {
        const current = instance.getCenter()
        viewChange.current?.({ lat: current.lat, lon: current.lng }, instance.getZoom())
      })
    })
    return () => {
      active = false
      map.current?.remove()
      map.current = null
      tile.current = null
    }
  }, [])
  useEffect(() => {
    void import('leaflet').then((L) => {
      if (!map.current || !layers.current) return
      tile.current?.remove()
      tile.current = L.tileLayer(tiles[basemap], {
        maxNativeZoom: 16,
        maxZoom: 19,
        attribution: 'USGS The National Map',
      }).addTo(map.current)
      layers.current.clearLayers()
      markers.forEach((item) =>
        L.circleMarker([item.lat, item.lon], {
          radius: 8,
          color: 'var(--brand-80)',
          fillColor: 'var(--brand-80)',
          fillOpacity: 1,
        }).addTo(layers.current!),
      )
      if (line.length > 1)
        L.polyline(
          line.map(([lon, lat]) => [lat, lon]),
          { color: 'var(--brand-80)', weight: 5 },
        ).addTo(layers.current)
      map.current.setView([center.lat, center.lon], zoom)
    })
  }, [basemap, center.lat, center.lon, line, markers, zoom])
  return <div ref={element} className="map-view" role="application" aria-label="Mapa" />
}
