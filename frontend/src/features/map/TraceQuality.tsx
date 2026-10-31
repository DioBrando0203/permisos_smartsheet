import { StatusAlert } from '../../components/ui'
import type { MapTrace } from './types'
import { TraceAlignmentNote } from './TraceAlignmentNote'

/** Explica cobertura estimada y separa datos FDOT de las reglas calculadas por el panel. */
export function TraceQuality({ result }: { result: MapTrace }) {
  const incomplete = result.warnings.includes('TRACE_GEOMETRY_INCOMPLETE')
  return (
    <>
      <TraceAlignmentNote result={result} />
      {result.warnings.includes('TRACE_PARTIAL') && (
        <StatusAlert tone="warning" title="Revisar recorrido incompleto">
          {result.unmatchedLengthMi === null
            ? 'Hay partes del dibujo sin vía cercana.'
            : `${(result.unmatchedLengthMi * 1609.344).toFixed(0)} m del dibujo quedan sin vía dentro de ${result.coverageRadiusM} m.`}{' '}
          Conservamos la línea punteada para revisarla. Agrega puntos siguiendo la curva o corrige los
          extremos.
        </StatusAlert>
      )}
      {incomplete && (
        <StatusAlert tone="warning" title="Geometría de vía incompleta">
          La fuente no permitió reconstruir todo el tramo entre los mileposts. Longitud no disponible; revisa
          las filas antes de copiarlas.
        </StatusAlert>
      )}
      {result.matchedPercent !== null && (
        <p className="map-note">
          Dibujo asociado a vías: {result.matchedPercent.toFixed(1)} % (estimado)
          {result.alignment === 'adjusted' || result.alignment === 'ambiguous' ? ', antes del ajuste' : ''}.
        </p>
      )}
      {result.adjustment && (
        <p className="map-note">
          Distancia de los extremos a la vía: inicio {distance(result.adjustment.startM)}; final{' '}
          {distance(result.adjustment.endM)}. Calculada por el panel con datos FDOT.
        </p>
      )}
    </>
  )
}

function distance(meters: number | null): string {
  return meters === null ? 'no disponible' : `${meters.toFixed(1)} m`
}
