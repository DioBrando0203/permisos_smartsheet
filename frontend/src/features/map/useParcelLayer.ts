import { useMemo } from 'react'
import type { MapViewState } from '../../components/map/MapView'
import { useParcelOutlines } from './hooks'
import { cellsFor, parcelMinZoom } from './lib/cells'

/** Límites de parcelas de la vista (PEN-33): sólo de cerca y con un aviso de qué pasa. */
export function useParcelLayer(enabled: boolean, view: MapViewState | null) {
  const close = Boolean(view && view.zoom >= parcelMinZoom)
  const cells = useMemo(() => (enabled && close && view ? cellsFor(view.bounds) : []), [enabled, close, view])
  const layer = useParcelOutlines(cells)
  const hint = !enabled
    ? null
    : !close || cells.length === 0
      ? `Acércate (zoom ${parcelMinZoom} o más) para ver las parcelas.`
      : layer.loading
        ? 'Cargando parcelas…'
        : layer.failed > 0
          ? 'Algunas parcelas no se pudieron cargar.'
          : layer.truncated
            ? 'Hay demasiadas parcelas en la zona: puede faltar alguna.'
            : null
  return { rings: enabled ? layer.rings : noRings, hint }
}

// Constante: un arreglo nuevo en cada render haría redibujar el mapa sin motivo.
const noRings: [number, number][][] = []
