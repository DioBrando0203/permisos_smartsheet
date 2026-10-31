import { Location24Regular } from '@fluentui/react-icons'
import { Button, LoadingNotice, StatusAlert } from '../../components/ui'
import { ApiError } from '../../lib/api'
import { errorMessage } from '../../lib/errorMessages'
import {
  JurisdictionSection,
  LocationSection,
  ParcelSection,
  RoadSection,
  SourcesSection,
} from './MapSections'
import type { MapPoint } from './types'

export function PointResult({
  result,
  loading,
  error,
  onRetry,
  preferRoadway = null,
}: {
  result?: MapPoint
  loading: boolean
  error: Error | null
  onRetry: () => void
  preferRoadway?: string | null
}) {
  if (loading) return <LoadingNotice>Consultando FDOT y FDACS…</LoadingNotice>
  if (error) return <MapError error={error} onRetry={onRetry} />
  if (!result) return <MapEmpty />
  const roads = [
    ...result.roads.filter((road) => road.roadwayId === preferRoadway),
    ...result.roads.filter((road) => road.roadwayId !== preferRoadway),
  ]
  return (
    <>
      <RoadSection road={roads[0]} nearby={roads.slice(1)} />
      <JurisdictionSection data={result.jurisdiction} />
      <LocationSection location={result.location} />
      <ParcelSection parcel={result.parcel} />
      <SourcesSection sources={result.sources} />
      {result.warnings.includes('SOURCE_FAILED') && (
        <StatusAlert tone="warning" title="Datos parciales">
          Una fuente GIS no respondió. Usa Actualizar para consultar de nuevo.
        </StatusAlert>
      )}
    </>
  )
}

export function MapEmpty({
  text = 'Busca un lugar arriba o haz clic sobre una calle del mapa.',
}: {
  text?: string
}) {
  return (
    <div className="map-empty">
      <Location24Regular aria-hidden="true" />
      <p>{text}</p>
    </div>
  )
}

export function MapError({ error, onRetry }: { error: Error; onRetry: () => void }) {
  const api = error instanceof ApiError ? error : null
  return (
    <StatusAlert tone="error" title="No se pudo consultar el mapa">
      <p>{errorMessage(api?.code ?? 'UNKNOWN', api?.message).text}</p>
      <Button appearance="secondary" onClick={onRetry}>
        Reintentar
      </Button>
    </StatusAlert>
  )
}
