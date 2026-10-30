import { Copy24Regular, Location24Regular } from '@fluentui/react-icons'
import { Badge, Button, CopyText, LoadingNotice, StatusAlert } from '../../components/ui'
import { ApiError } from '../../lib/api'
import { errorMessage } from '../../lib/errorMessages'
import { ospText } from './lib/ospRow'
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
      <Road road={result.roads[0]} alternatives={result.roads.slice(1)} />
      <Place result={result} />
      <Sources sources={result.sources} />
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
    return <Empty text="Haz clic en A y luego en B sobre la misma vía. Escape cancela el punto B." />
  if (loading) return <LoadingNotice>Calculando el tramo…</LoadingNotice>
  if (error) return <MapError error={error} onRetry={onRetry} />
  if (!result) return null
  return (
    <>
      <Road road={result.road} alternatives={[]} />
      <section className="map-result-section">
        <h2>Tramo</h2>
        <p>
          Milepost {result.beginMilepost.toFixed(3)} a {result.endMilepost.toFixed(3)} ·{' '}
          {result.lengthMi.toFixed(3)} mi
        </p>
      </section>
      <Jurisdiction data={result.jurisdiction} />
      <Osp segment={result} />
    </>
  )
}
function Osp({ segment }: { segment: MapSegment }) {
  const copy = () => void navigator.clipboard.writeText(ospText(segment))
  const row = segment.ospRow
  return (
    <section className="map-result-section">
      <h2>Fila para OSP</h2>
      <dl>
        <dt>County</dt>
        <dd>{row.county ?? '—'}</dd>
        <dt>State Road ID</dt>
        <dd>{row.stateRoadId}</dd>
        <dt>Section Number</dt>
        <dd>{row.sectionNumber ?? '—'}</dd>
        <dt>Beginning Milepost</dt>
        <dd>{row.beginningMilepost.toFixed(3)}</dd>
        <dt>Ending Milepost</dt>
        <dd>{row.endingMilepost.toFixed(3)}</dd>
      </dl>
      <Button appearance="primary" onClick={copy}>
        <Copy24Regular aria-hidden="true" />
        Copiar para OSP
      </Button>
    </section>
  )
}
function Place({ result }: { result: MapPoint }) {
  return (
    <>
      <Jurisdiction data={result.jurisdiction} />
      <section className="map-result-section">
        <h2>Ubicación</h2>
        <p>
          {result.location.county ?? 'Condado no disponible'} ·{' '}
          {result.location.city ?? 'Zona no incorporada'} · {result.location.zip ?? 'ZIP no disponible'}
        </p>
      </section>
      <section className="map-result-section">
        <h2>Parcela</h2>
        {result.parcel ? (
          <>
            <CopyText value={result.parcel.parcelId} />
            <p>{result.parcel.useLabel ?? result.parcel.useCode ?? 'Uso no disponible'}</p>
            {result.parcel.ownerName && <p>Según el tasador (registro público): {result.parcel.ownerName}</p>}
          </>
        ) : (
          <p>No se encontró una parcela en este punto.</p>
        )}
      </section>
    </>
  )
}
function Road({ road, alternatives }: { road?: MapPoint['roads'][number]; alternatives: MapPoint['roads'] }) {
  return (
    <section className="map-result-section">
      <h1>
        <Location24Regular aria-hidden="true" /> Vía
      </h1>
      {road ? (
        <>
          <Badge>{road.kind === 'state' ? 'Estatal' : road.kind === 'county' ? 'De condado' : 'Otra'}</Badge>
          <p>
            <strong>{road.route ?? road.localName ?? 'Vía sin nombre'}</strong>
          </p>
          <p>
            ID {road.roadwayId} · Sección {road.section ?? '—'} · Milepost{' '}
            {road.milepost?.toFixed(3) ?? 'No disponible'}
          </p>
          {alternatives.length > 0 && (
            <p>
              También cerca:{' '}
              {alternatives.map((item) => `${item.route ?? item.roadwayId} (${item.distanceM} m)`).join(', ')}
            </p>
          )}
        </>
      ) : (
        <p>No hay una vía a menos de 25 m.</p>
      )}
    </section>
  )
}
function Jurisdiction({ data }: { data: MapPoint['jurisdiction'] }) {
  return (
    <section className="map-result-section">
      <h2>De quién es la calle</h2>
      <p>
        <strong>{data.name ?? data.authority}</strong> · confianza{' '}
        {data.confidence === 'high' ? 'Alta' : data.confidence === 'medium' ? 'Media' : 'Baja'}
      </p>
      <p>{data.note}</p>
    </section>
  )
}
function Sources({ sources }: { sources: MapPoint['sources'] }) {
  return (
    <section className="map-result-section">
      <h2>Fuentes</h2>
      <ul>
        {sources.map((source) => (
          <li key={source.id}>
            {source.id}: {source.status === 'ok' ? 'Disponible' : 'No disponible'}
          </li>
        ))}
      </ul>
    </section>
  )
}
function Empty({ text = 'Haz clic sobre una calle o pega coordenadas.' }: { text?: string }) {
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
