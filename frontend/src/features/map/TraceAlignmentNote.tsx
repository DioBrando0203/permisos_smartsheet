import { StatusAlert } from '../../components/ui'
import type { MapTrace } from './types'

export function TraceAlignmentNote({ result }: { result: MapTrace }) {
  return (
    <>
      {(result.alignment === 'adjusted' || result.alignment === 'ambiguous') && (
        <p className="map-note">
          Recorrido reconstruido sobre las vías. Los puntos se ajustaron dentro de {result.radiusM} m; las
          curvas y los cambios de vía pueden alargar, acortar o dividir la línea.
        </p>
      )}
      {result.alignment === 'unavailable' && (
        <StatusAlert tone="warning" title="No se pudo ajustar todo el recorrido">
          Se muestra la detección estricta. Acerca los puntos a la vía o agrega un punto en cada giro.
        </StatusAlert>
      )}
      {result.alignment === 'ambiguous' && (
        <StatusAlert tone="warning" title="Hay recorridos alternativos similares">
          Revisa la vía seleccionada o agrega un punto sobre la vía deseada.
        </StatusAlert>
      )}
      {result.warnings.includes('TRACE_CONNECTIONS_INFERRED') && (
        <p className="map-note">
          Los cambios de vía se calcularon por su conexión geométrica. Revisa cruces a desnivel; esta capa no
          confirma giros ni elevación.
        </p>
      )}
    </>
  )
}
