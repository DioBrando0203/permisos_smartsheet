import { useEffect, useMemo, useState } from 'react'
import { useSearchParams } from 'react-router'
import { MapView } from '../../components/map/MapView'
import { Button, StatusAlert } from '../../components/ui'
import { useMapPoint, useMapSegment } from './hooks'
import { parseCoordinates, type Coordinates } from './lib/coordinates'
import { readMapUrl, writeMapUrl } from './lib/mapUrl'
import { PointResult, SegmentResult } from './MapResults'

const initial = { lat: 26.1, lon: -80.25 }
type Mode = 'point' | 'segment'

export function MapPage() {
  const [params, setParams] = useSearchParams()
  const saved = useMemo(() => readMapUrl(params), [params])
  const [mode, setMode] = useState<Mode>(saved.a && saved.b ? 'segment' : 'point')
  const [a, setA] = useState<Coordinates | null>(saved.a ?? saved.point)
  const [b, setB] = useState<Coordinates | null>(saved.b)
  const [field, setField] = useState('')
  const [inputError, setInputError] = useState('')
  const [basemap, setBasemap] = useState<'streets' | 'satellite'>(() =>
    localStorage.getItem('map-basemap') === 'satellite' ? 'satellite' : 'streets',
  )
  const point = useMapPoint(mode === 'point' ? a : null)
  const segment = useMapSegment(mode === 'segment' ? a : null, mode === 'segment' ? b : null)
  useEffect(() => {
    setParams(writeMapUrl(mode, a, mode === 'segment' ? b : null), { replace: true })
  }, [a, b, mode, setParams])
  useEffect(() => {
    localStorage.setItem('map-basemap', basemap)
  }, [basemap])
  useEffect(() => {
    const escape = (event: KeyboardEvent) => {
      if (event.key === 'Escape') setB(null)
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
  const submit = () => {
    const parsed = parseCoordinates(field)
    if (!parsed) {
      setInputError('Use latitud y longitud, por ejemplo 25.771778, -80.263610.')
      return
    }
    setInputError('')
    choose(parsed)
  }
  const current = mode === 'point' ? point.data : segment.data?.start
  const markers = [a, b].filter((value): value is Coordinates => Boolean(value))
  return (
    <section className="map-page">
      <div className="map-page__canvas">
        <MapToolbar
          mode={mode}
          setMode={(value) => {
            setMode(value)
            setB(null)
          }}
          field={field}
          setField={setField}
          onSubmit={submit}
          basemap={basemap}
          setBasemap={setBasemap}
          error={inputError}
        />
        <MapView
          center={a ?? initial}
          zoom={a ? 15 : 10}
          markers={markers}
          line={segment.data?.geometry.coordinates ?? []}
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

function MapToolbar({
  mode,
  setMode,
  field,
  setField,
  onSubmit,
  basemap,
  setBasemap,
  error,
}: {
  mode: Mode
  setMode: (value: Mode) => void
  field: string
  setField: (value: string) => void
  onSubmit: () => void
  basemap: 'streets' | 'satellite'
  setBasemap: (value: 'streets' | 'satellite') => void
  error: string
}) {
  return (
    <div className="map-toolbar">
      <div className="map-toolbar__modes" aria-label="Modo de consulta">
        <Button appearance={mode === 'point' ? 'primary' : 'secondary'} onClick={() => setMode('point')}>
          Punto
        </Button>
        <Button appearance={mode === 'segment' ? 'primary' : 'secondary'} onClick={() => setMode('segment')}>
          Tramo
        </Button>
      </div>
      <label className="map-toolbar__coordinates">
        Coordenadas
        <input
          value={field}
          onChange={(event) => setField(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === 'Enter') onSubmit()
          }}
          placeholder="25.771778, -80.263610"
        />
        {error && <span role="alert">{error}</span>}
      </label>
      <Button appearance="secondary" onClick={onSubmit}>
        Consultar
      </Button>
      <label className="map-toolbar__base">
        Mapa base
        <select
          value={basemap}
          onChange={(event) => setBasemap(event.target.value as 'streets' | 'satellite')}
        >
          <option value="streets">Calles (USGS)</option>
          <option value="satellite">Satélite (USGS)</option>
        </select>
      </label>
    </div>
  )
}
