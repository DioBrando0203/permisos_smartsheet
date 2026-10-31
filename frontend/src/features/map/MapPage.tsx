import { useEffect, useRef, useState } from 'react'
import { useSearchParams } from 'react-router'
import { MapView, type Basemap, type MapFocus, type MapViewState } from '../../components/map/MapView'
import { basemapChoices } from '../../components/map/tileSources'
import { Button } from '../../components/ui'
import type { MapScope } from './area'
import { useMapArea, useMapPoint, useMapTrace } from './hooks'
import type { Coordinates } from './lib/coordinates'
import { readMapUrl, writeMapUrl, type MapMode } from './lib/mapUrl'
import { readChoice, readText, saveChoice } from './lib/preferences'
import { PointResult } from './MapResults'
import { MapToolbar, type MapLayers } from './MapToolbar'
import { TraceResult } from './TraceResult'
import { useParcelLayer } from './useParcelLayer'
import { useMapDrawing } from './useMapDrawing'
import { useTraceDrawing } from './useTraceDrawing'

const closeZoom = 16
const noArea: [number, number][][] = []
const onOff = ['on', 'off'] as const
const savedLayers = (): MapLayers => ({
  roads: readChoice('map-roads', onOff, 'off') === 'on',
  parcels: readChoice('map-parcels', onOff, 'off') === 'on',
})

export function MapPage() {
  const [params, setParams] = useSearchParams()
  const [saved] = useState(() => readMapUrl(params))
  const [mode, setMode] = useState<MapMode>(saved.trace ? 'trace' : 'point')
  const [a, setA] = useState<Coordinates | null>(saved.point)
  const trace = useTraceDrawing(saved.trace)
  const [focus, setFocus] = useState<MapFocus | null>(() => {
    const first = saved.trace?.[0] ?? saved.point
    return first ? { ...first, zoom: closeZoom } : null
  })
  const [basemap, setBasemap] = useState<Basemap>(() => readChoice('map-basemap', basemapChoices, 'streets'))
  const [layers, setLayers] = useState<MapLayers>(savedLayers)
  const [view, setView] = useState<MapViewState | null>(null)
  // Vía del resultado elegido en el buscador: el panel la pone primero (un cruce toca dos vías).
  const [preferred, setPreferred] = useState<string | null>(null)
  const [scope, setScope] = useState<MapScope>(() => ({
    county: readText('map-county'),
    city: readText('map-county') ? readText('map-city') : null,
  }))
  const area = useMapArea(scope)
  // Sólo un cambio de zona hecho por la persona encuadra el mapa; la guardada no tapa la URL.
  const fitArea = useRef(false)
  const point = useMapPoint(mode === 'point' ? a : null)
  const result = useMapTrace(mode === 'trace' ? trace.finished : null)
  const reading = mode === 'point' ? point : result
  const drawing = useMapDrawing(mode, a, trace, result.data)
  const parcels = useParcelLayer(layers.parcels, view)
  useEffect(() => {
    setParams(writeMapUrl(mode, a, trace.finished), { replace: true })
  }, [a, trace.finished, mode, setParams])
  useEffect(() => saveChoice('map-basemap', basemap), [basemap])
  useEffect(() => {
    saveChoice('map-county', scope.county ?? '')
    saveChoice('map-city', scope.city ?? '')
  }, [scope])
  useEffect(() => {
    if (!fitArea.current || !area.data) return
    fitArea.current = false
    setFocus({ bounds: area.data.bounds })
  }, [area.data])
  useEffect(() => {
    saveChoice('map-roads', layers.roads ? 'on' : 'off')
    saveChoice('map-parcels', layers.parcels ? 'on' : 'off')
  }, [layers])
  useEffect(() => {
    const keys = (event: KeyboardEvent) => {
      if (mode !== 'trace' || event.target instanceof HTMLInputElement) return
      if (event.key === 'Enter') trace.finish()
      if (event.key === 'Escape') trace.clear()
    }
    window.addEventListener('keydown', keys)
    return () => window.removeEventListener('keydown', keys)
  })
  const choose = (next: Coordinates) => (mode === 'point' ? setA(next) : trace.add(next))
  return (
    <section className="map-page">
      <div className="map-page__canvas">
        <MapToolbar
          mode={mode}
          scope={scope}
          basemap={basemap}
          layers={layers}
          hint={hint(mode, trace.vertices.length, trace.drawing)}
          parcelHint={parcels.hint}
          onMode={setMode}
          onScope={(next) => {
            fitArea.current = Boolean(next.county)
            setScope(next)
          }}
          onBasemap={setBasemap}
          onLayers={setLayers}
          onSelect={(next, _label, roadway) => {
            setPreferred(roadway)
            choose(next)
            setFocus({ ...next, zoom: closeZoom })
          }}
        />
        <MapView
          focus={drawing.focus ?? focus}
          markers={drawing.markers}
          lines={drawing.lines}
          outlines={parcels.rings}
          area={(scope.county && area.data?.outline) || noArea}
          basemap={basemap}
          roads={layers.roads}
          drawing={mode === 'trace' && trace.drawing}
          onMapClick={(next) => {
            setPreferred(null)
            choose(next)
          }}
          onMapDoubleClick={() => mode === 'trace' && trace.finish()}
          onViewChange={setView}
        />
      </div>
      <aside className="map-page__panel" aria-live="polite" aria-label="Resultados del mapa">
        <Button
          appearance="secondary"
          size="sm"
          onClick={reading.refresh}
          disabled={reading.isFetching || (mode === 'point' ? !a : !trace.finished)}
        >
          {reading.isFetching ? 'Actualizando…' : 'Actualizar'}
        </Button>
        {mode === 'point' ? (
          <PointResult
            result={point.data}
            preferRoadway={preferred}
            loading={point.isLoading}
            error={point.error}
            onRetry={point.refresh}
          />
        ) : (
          <TraceResult
            vertices={trace.vertices.length}
            drawing={trace.drawing}
            result={result.data}
            loading={result.isLoading}
            error={result.error}
            onFinish={trace.finish}
            onUndo={trace.undo}
            onClear={trace.clear}
            onRetry={result.refresh}
          />
        )}
      </aside>
    </section>
  )
}

function hint(mode: MapMode, vertices: number, drawing: boolean): string {
  if (mode === 'point') return 'Busca un lugar o haz clic sobre una calle.'
  if (!drawing) return 'Trazo listo. Un clic empieza otro.'
  if (vertices === 0) return 'Marca el inicio sobre la vía y sigue el recorrido con más clics.'
  return 'Sigue la vía con más clics; doble clic o Enter para terminar. Escape lo borra.'
}
