import { Button, LoadingNotice, StatusAlert } from '../../components/ui'
import { MapEmpty, MapError } from './MapResults'
import { SourcesSection } from './MapSections'
import type { MapTrace } from './types'
import { TraceQuality } from './TraceQuality'
import { WorkLocationTable } from './WorkLocationTable'

type Props = {
  vertices: number
  drawing: boolean
  result?: MapTrace
  loading: boolean
  error: Error | null
  onFinish: () => void
  onUndo: () => void
  onClear: () => void
  onRetry: () => void
}

/** Panel del modo Trazo: controles del dibujo y, al terminar, la tabla Work Location. */
export function TraceResult({ vertices, drawing, onFinish, onUndo, onClear, ...state }: Props) {
  return (
    <>
      <div className="map-trace-controls" role="group" aria-label="Trazo">
        <span>{vertices === 1 ? '1 punto' : `${vertices} puntos`}</span>
        <Button size="sm" onClick={onFinish} disabled={!drawing || vertices < 2}>
          Terminar
        </Button>
        <Button size="sm" appearance="secondary" onClick={onUndo} disabled={vertices === 0}>
          Deshacer
        </Button>
        <Button size="sm" appearance="secondary" onClick={onClear} disabled={vertices === 0}>
          Borrar
        </Button>
      </div>
      {drawing ? <DrawingHelp vertices={vertices} /> : <TraceBody {...state} />}
    </>
  )
}

function DrawingHelp({ vertices }: { vertices: number }) {
  if (vertices === 0)
    return (
      <MapEmpty text="Haz clic sobre la vía donde empieza el trabajo y sigue el recorrido con más clics. Doble clic, Enter o Terminar calculan la tabla." />
    )
  return (
    <p className="map-note">Sigue la vía con más clics. Doble clic, Enter o Terminar calculan la tabla.</p>
  )
}

function TraceBody({
  result,
  loading,
  error,
  onRetry,
}: Pick<Props, 'result' | 'loading' | 'error' | 'onRetry'>) {
  if (loading) return <LoadingNotice>Calculando el trazo…</LoadingNotice>
  if (error) return <MapError error={error} onRetry={onRetry} />
  if (!result) return null
  if (result.rows.length === 0)
    return (
      <>
        <StatusAlert tone="info" title="Sin vías en el trazo">
          El trazo no sigue ninguna vía del FDOT a menos de 25 m. Dibújalo sobre la calle.
        </StatusAlert>
        <TraceQuality result={result} />
        <SourcesSection sources={result.sources} />
      </>
    )
  const roadCount = new Set(result.rows.map((row) => row.roadwayId)).size
  const roads = roadCount === 1 ? '1 vía' : `${roadCount} vías`
  return (
    <>
      <TraceQuality result={result} />
      <WorkLocationTable rows={result.rows} />
      <p className="map-note">
        {result.lengthMi === null
          ? 'Longitud no disponible'
          : `Recorrido sobre geometría FDOT: ${result.lengthMi.toFixed(3)} mi`}{' '}
        sobre {roads}.
      </p>
      {result.lengthMi !== null && Math.abs(result.inputLengthMi - result.lengthMi) >= 0.001 && (
        <p className="map-note">Línea marcada: {result.inputLengthMi.toFixed(3)} mi.</p>
      )}
      {result.warnings.includes('NOT_STATE_ROAD') && (
        <p className="map-note">"No estatal": la vía no es del Sistema Estatal y OSP no la acepta.</p>
      )}
      <SourcesSection sources={result.sources} />
      {result.warnings.includes('SOURCE_FAILED') && (
        <StatusAlert tone="warning" title="Datos parciales">
          Una fuente no respondió. Usa Actualizar para consultar de nuevo.
        </StatusAlert>
      )}
    </>
  )
}
