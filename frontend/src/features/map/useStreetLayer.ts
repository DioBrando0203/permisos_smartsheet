import { useMemo } from 'react'
import type { MapOverlay, MapViewState } from '../../components/map/MapView'
import { useStreetLines } from './hooks'
import { cellsFor, streetCellDegrees, streetMinZoom } from './lib/cells'
import { streetTone, streetTooltip, toneClass, toneLabels, type StreetTone } from './lib/jurisdiction'
import type { StreetLine, TraceStreet } from './streets'

const order = Object.keys(toneLabels) as StreetTone[]

/** Líneas de color de una calle: una por trayectoria, con su texto al pasar el cursor. */
export function streetOverlays(streets: (StreetLine | TraceStreet)[], weight?: number): MapOverlay[] {
  return streets.flatMap((street) => {
    const className = `map-street ${toneClass(streetTone(street.authority))}`
    const tooltip = streetTooltip(street)
    return street.paths.map((coordinates) => ({ coordinates, className, weight, tooltip }))
  })
}

/** Calles coloreadas por responsable (PEN-41): sólo de cerca y con un aviso de qué pasa. */
export function useStreetLayer(enabled: boolean, view: MapViewState | null) {
  const close = Boolean(view && view.zoom >= streetMinZoom)
  const cells = useMemo(
    () => (enabled && close && view ? cellsFor(view.bounds, streetCellDegrees) : []),
    [enabled, close, view],
  )
  const layer = useStreetLines(cells)
  const overlays = useMemo(
    () => (enabled ? streetOverlays(layer.streets) : noOverlays),
    [enabled, layer.streets],
  )
  // La leyenda sólo muestra los colores que hay en la vista, en el orden de la tabla.
  const tones = useMemo(() => {
    const present = new Set(layer.streets.map((street) => streetTone(street.authority)))
    return enabled ? order.filter((tone) => present.has(tone)) : []
  }, [enabled, layer.streets])
  return { overlays, tones, hint: enabled ? hint(close && cells.length > 0, layer) : null }
}

function hint(close: boolean, layer: ReturnType<typeof useStreetLines>): string | null {
  if (!close) return `Acércate (zoom ${streetMinZoom} o más) para ver de quién son las calles.`
  if (layer.loading) return 'Cargando calles del condado…'
  if (layer.failed > 0) return 'Algunas calles no se pudieron cargar.'
  if (!layer.available) return 'Por ahora sólo St. Johns publica quién mantiene cada calle.'
  if (layer.truncated) return 'Hay demasiadas calles en la zona: puede faltar alguna.'
  return null
}

// Constante: un arreglo nuevo en cada render haría redibujar el mapa sin motivo.
const noOverlays: MapOverlay[] = []
