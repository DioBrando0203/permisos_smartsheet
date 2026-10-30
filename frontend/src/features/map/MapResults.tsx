import { Location24Regular } from '@fluentui/react-icons'
import { Button, LoadingNotice, StatusAlert } from '../../components/ui'
import { ApiError } from '../../lib/api'
import { errorMessage } from '../../lib/errorMessages'
import {
  JurisdictionSection,
  LocationSection,
  OspSection,
  ParcelSection,
  RoadSection,
  SourcesSection,
} from './MapSections'
import type { MapPoint, MapSegment } from './types'

export function PointResult({
  result,
  loading,
  error,
  onRetry,
}: {
  result?: MapPoint
  loading: boolean
  error: Error | null
  onRetry: () => void
}) {
  if (loading) return <LoadingNotice>Consultando FDOT y FDACS…</LoadingNotice>
  if (error) return <MapError error={error} onRetry={onRetry} />
  if (!result) return <Empty />
  return (
    <>
      <RoadSection road={result.roads[0]} nearby={result.roads.slice(1)} />
      <JurisdictionSection data={result.jurisdiction} />
      <LocationSection location={result.location} />
      <ParcelSection parcel={result.parcel} />
      <SourcesSection sources={result.sources} />
    </>
  )
}

export function SegmentResult({
  result,
  loading,
  error,
  waiting,
  onRetry,
}: {
  result?: MapSegment
  loading: boolean
  error: Error | null
  waiting: boolean
  onRetry: () => void
}) {
  if (waiting)
    return (
      <Empty text="Marca el punto A y luego el punto B sobre la misma vía, con un clic o con el buscador." />
    )
  if (loading) return <LoadingNotice>Calculando el tramo…</LoadingNotice>
  if (error) return <MapError error={error} onRetry={onRetry} />
  if (!result) return null
  return (
    <>
      <OspSection segment={result} />
      <RoadSection road={result.road} nearby={[]} />
      <p className="map-note">
        Tramo de {result.lengthMi.toFixed(3)} mi, del milepost {result.beginMilepost.toFixed(3)} al{' '}
        {result.endMilepost.toFixed(3)}.
      </p>
      <JurisdictionSection data={result.jurisdiction} />
      <SourcesSection sources={result.start.sources} />
    </>
  )
}

function Empty({ text = 'Busca un lugar arriba o haz clic sobre una calle del mapa.' }: { text?: string }) {
  return (
    <div className="map-empty">
      <Location24Regular aria-hidden="true" />
      <p>{text}</p>
    </div>
  )
}

function MapError({ error, onRetry }: { error: Error; onRetry: () => void }) {
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
