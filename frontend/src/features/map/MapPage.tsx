import { useEffect, useMemo, useState } from 'react'
import { useSearchParams } from 'react-router'
import { MapView, type Basemap, type MapFocus, type MapMarker } from '../../components/map/MapView'
import { basemapChoices } from '../../components/map/tileSources'
import { StatusAlert } from '../../components/ui'
import { useMapPoint, useMapSegment } from './hooks'
import type { Coordinates } from './lib/coordinates'
import { readMapUrl, writeMapUrl } from './lib/mapUrl'
import { readChoice, saveChoice } from './lib/preferences'
import { PointResult, SegmentResult } from './MapResults'
import { MapToolbar, type Mode } from './MapToolbar'

const noLine: [number, number][] = []
const closeZoom = 16

export function MapPage() {
  const [params, setParams] = useSearchParams()
  const saved = useMemo(() => readMapUrl(params), [params])
  const [mode, setMode] = useState<Mode>(saved.a && saved.b ? 'segment' : 'point')
  const [a, setA] = useState<Coordinates | null>(saved.a ?? saved.point)
  const [b, setB] = useState<Coordinates | null>(saved.b)
  const [focus, setFocus] = useState<MapFocus | null>(() => {
    const first = saved.a ?? saved.point
    return first ? { ...first, zoom: closeZoom } : null
  })
  const [basemap, setBasemap] = useState<Basemap>(() => readChoice('map-basemap', basemapChoices, 'streets'))
  const [roads, setRoads] = useState(() => readChoice('map-roads', ['on', 'off'], 'off') === 'on')
  const point = useMapPoint(mode === 'point' ? a : null)
  const segment = useMapSegment(mode === 'segment' ? a : null, mode === 'segment' ? b : null)
  useEffect(() => {
    setParams(writeMapUrl(mode, a, mode === 'segment' ? b : null), { replace: true })
  }, [a, b, mode, setParams])
  useEffect(() => saveChoice('map-basemap', basemap), [basemap])
  useEffect(() => saveChoice('map-roads', roads ? 'on' : 'off'), [roads])
  useEffect(() => {
    const escape = (event: KeyboardEvent) => {
      if (event.key === 'Escape' && !(event.target instanceof HTMLInputElement)) setB(null)
    }
    window.addEventListener('keydown', escape)
    return () => window.removeEventListener('keydown', escape)
  }, [])
  const choose = (next: Coordinates) => {
    if (mode === 'point' || (a && b)) {
      setA(next)
      setB(null)
    } else if (!a) setA(next)
    else setB(next)
  }
  const markers = useMemo<MapMarker[]>(() => {
    if (mode === 'point') return a ? [a] : []
    const labeled: MapMarker[] = []
    if (a) labeled.push({ ...a, label: 'A' })
    if (b) labeled.push({ ...b, label: 'B' })
    return labeled
  }, [a, b, mode])
  const current = mode === 'point' ? point.data : segment.data?.start
  return (
    <section className="map-page">
      <div className="map-page__canvas">
        <MapToolbar
          mode={mode}
          basemap={basemap}
          roads={roads}
          hint={hint(mode, a, b)}
          onMode={(value) => {
            setMode(value)
            setB(null)
          }}
          onBasemap={setBasemap}
          onRoads={setRoads}
          onSelect={(next) => {
            choose(next)
            setFocus({ ...next, zoom: closeZoom })
          }}
        />
        <MapView
          focus={focus}
          markers={markers}
          line={(mode === 'segment' && segment.data?.geometry.coordinates) || noLine}
          basemap={basemap}
          roads={roads}
          onMapClick={choose}
        />
      </div>
      <aside className="map-page__panel" aria-live="polite" aria-label="Resultados del mapa">
        {mode === 'point' ? (
          <PointResult
            result={point.data}
            loading={point.isLoading}
            error={point.error}
            onRetry={() => void point.refetch()}
          />
        ) : (
          <SegmentResult
            result={segment.data}
            loading={segment.isLoading}
            error={segment.error}
            waiting={!a || !b}
            onRetry={() => void segment.refetch()}
          />
        )}
        {current?.warnings.includes('SOURCE_FAILED') && (
          <StatusAlert tone="warning" title="Datos parciales">
            Una fuente GIS no respondió. Puede reintentar la consulta.
          </StatusAlert>
        )}
      </aside>
    </section>
  )
}

function hint(mode: Mode, a: Coordinates | null, b: Coordinates | null): string {
  if (mode === 'point') return 'Busca un lugar o haz clic sobre una calle.'
  if (!a) return 'Marca el punto A: búscalo o haz clic sobre la vía.'
  if (!b) return 'Ahora marca el punto B sobre la misma vía. Escape lo cancela.'
  return 'Tramo listo. Un clic o una búsqueda empieza otro.'
}
