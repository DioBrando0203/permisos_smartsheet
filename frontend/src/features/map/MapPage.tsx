import { useEffect, useMemo, useState } from 'react'
import { useSearchParams } from 'react-router'
import { MapView, type MapFocus, type MapMarker } from '../../components/map/MapView'
import { Button, StatusAlert } from '../../components/ui'
import { useMapPoint, useMapSegment } from './hooks'
import type { Coordinates } from './lib/coordinates'
import { readMapUrl, writeMapUrl } from './lib/mapUrl'
import { PointResult, SegmentResult } from './MapResults'
import { MapSearchBox } from './MapSearchBox'

type Mode = 'point' | 'segment'
type Basemap = 'streets' | 'satellite'
const noLine: [number, number][] = []
const closeZoom = 16

function savedBasemap(): Basemap {
  try {
    return localStorage.getItem('map-basemap') === 'satellite' ? 'satellite' : 'streets'
  } catch {
    return 'streets'
  }
}

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
  const [basemap, setBasemap] = useState<Basemap>(savedBasemap)
  const point = useMapPoint(mode === 'point' ? a : null)
  const segment = useMapSegment(mode === 'segment' ? a : null, mode === 'segment' ? b : null)
  useEffect(() => {
    setParams(writeMapUrl(mode, a, mode === 'segment' ? b : null), { replace: true })
  }, [a, b, mode, setParams])
  useEffect(() => {
    try {
      localStorage.setItem('map-basemap', basemap)
    } catch {
      // Sin almacenamiento (modo privado): sólo se pierde la preferencia.
    }
  }, [basemap])
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
        <div className="map-toolbar">
          <div className="map-toolbar__modes" role="group" aria-label="Modo de consulta">
            {(['point', 'segment'] as const).map((value) => (
              <Button
                key={value}
                appearance={mode === value ? 'primary' : 'secondary'}
                aria-pressed={mode === value}
                onClick={() => {
                  setMode(value)
                  setB(null)
                }}
              >
                {value === 'point' ? 'Punto' : 'Tramo'}
              </Button>
            ))}
          </div>
          <MapSearchBox
            onSelect={(next) => {
              choose(next)
              setFocus({ ...next, zoom: closeZoom })
            }}
          />
          <label className="map-toolbar__base">
            Mapa base
            <select value={basemap} onChange={(event) => setBasemap(event.target.value as Basemap)}>
              <option value="streets">Calles (USGS)</option>
              <option value="satellite">Satélite (USGS)</option>
            </select>
          </label>
          <p className="map-toolbar__hint">{hint(mode, a, b)}</p>
        </div>
        <MapView
          focus={focus}
          markers={markers}
          line={(mode === 'segment' && segment.data?.geometry.coordinates) || noLine}
          basemap={basemap}
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
