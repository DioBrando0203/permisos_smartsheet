import {
  Building20Regular,
  Checkmark16Regular,
  Copy24Regular,
  DocumentText20Regular,
  Location20Regular,
  Road20Regular,
} from '@fluentui/react-icons'
import { useState, type ReactNode } from 'react'
import { Badge, Button, CopyText } from '../../components/ui'
import { ospText } from './lib/ospRow'
import type { MapPoint, MapSegment, RoadMatch } from './types'

const kindLabel = { state: 'Vía estatal', county: 'Vía de condado', other: 'Vía local' }
const confidence = {
  high: { text: 'Confianza alta', tone: 'info' },
  medium: { text: 'Confianza media', tone: 'warning' },
  low: { text: 'Aproximación', tone: 'warning' },
} as const
const sourceNames: Record<string, string> = {
  fdot_lrs: 'Vías y milepost (FDOT)',
  fdot_state_roads: 'Vías estatales (FDOT)',
  fdot_county_roads: 'Vías de condado (FDOT)',
  fdot_local_names: 'Nombres de calles (FDOT)',
  fdot_counties: 'Condados (FDOT)',
  fdot_cities: 'Ciudades (FDOT)',
  fdot_zip: 'Códigos ZIP (FDOT)',
  fdacs_parcels: 'Parcelas (FDACS)',
}

function Section({ icon, title, children }: { icon: ReactNode; title: string; children: ReactNode }) {
  return (
    <section className="map-result-section">
      <h2>
        {icon}
        {title}
      </h2>
      {children}
    </section>
  )
}

function Field({ label, value, copy }: { label: string; value: string | null; copy?: string }) {
  return (
    <div className="map-field">
      <dt>{label}</dt>
      <dd>
        {value === null ? (
          <span className="map-field__empty">No disponible</span>
        ) : copy ? (
          <CopyText value={value} label={`Copiar ${copy}`} />
        ) : (
          value
        )}
      </dd>
    </div>
  )
}

const mp = (value: number | null) => (value === null ? null : value.toFixed(3))

export function RoadSection({ road, nearby }: { road?: RoadMatch; nearby: RoadMatch[] }) {
  if (!road)
    return (
      <Section icon={<Road20Regular aria-hidden="true" />} title="Vía">
        <p>No hay una vía a menos de 25 m. Acércate más a la calle y vuelve a hacer clic.</p>
      </Section>
    )
  return (
    <Section icon={<Road20Regular aria-hidden="true" />} title="Vía">
      <p className="map-road-title">
        <strong>{road.route ?? road.localName ?? 'Vía sin nombre'}</strong>
        <Badge tone={road.kind === 'state' ? 'info' : 'neutral'}>{kindLabel[road.kind]}</Badge>
      </p>
      {road.route && road.localName && <p className="map-road-subtitle">{road.localName}</p>}
      <dl className="map-fields">
        <Field label="Milepost" value={mp(road.milepost)} copy="milepost" />
        <Field label="ID de vía" value={road.roadwayId} copy="ID de vía" />
        <Field label="Sección" value={road.section} />
        {road.distanceM > 0 && <Field label="Distancia al clic" value={`${road.distanceM} m`} />}
      </dl>
      {nearby.length > 0 && (
        <details className="map-nearby">
          <summary>Otras vías cerca ({nearby.length})</summary>
          <ul>
            {nearby.map((item) => (
              <li key={item.roadwayId}>
                {item.route ?? item.localName ?? item.roadwayId} · MP {mp(item.milepost) ?? '—'} · a{' '}
                {item.distanceM} m
              </li>
            ))}
          </ul>
        </details>
      )}
    </Section>
  )
}

export function JurisdictionSection({ data }: { data: MapPoint['jurisdiction'] }) {
  const level = confidence[data.confidence]
  const name = data.authority === 'FDOT' ? 'FDOT (Estado de Florida)' : (data.name ?? 'No identificada')
  return (
    <Section icon={<Building20Regular aria-hidden="true" />} title="De quién es la calle">
      <p className="map-road-title">
        <strong>{name}</strong>
        <Badge tone={level.tone}>{level.text}</Badge>
      </p>
      {data.note && <p className="map-note">{data.note}</p>}
    </Section>
  )
}

export function LocationSection({ location }: { location: MapPoint['location'] }) {
  return (
    <Section icon={<Location20Regular aria-hidden="true" />} title="Ubicación">
      <dl className="map-fields">
        <Field label="Condado" value={location.county} />
        <Field label="Ciudad" value={location.city ?? (location.county ? 'Zona no incorporada' : null)} />
        <Field label="ZIP" value={location.zip} />
        <Field label="Distrito FDOT" value={location.fdotDistrict} />
      </dl>
    </Section>
  )
}

export function ParcelSection({ parcel }: { parcel: MapPoint['parcel'] }) {
  return (
    <Section icon={<DocumentText20Regular aria-hidden="true" />} title="Parcela">
      {parcel ? (
        <dl className="map-fields">
          <Field label="Parcela" value={parcel.parcelId} copy="parcela" />
          <Field
            label="Uso"
            value={parcel.useLabel ?? (parcel.useCode ? `Código DOR ${parcel.useCode}` : null)}
          />
          <Field label="Propietario (tasador)" value={parcel.ownerName} />
        </dl>
      ) : (
        <p>Sin parcela en este punto: suele pasar cuando el clic cae sobre la calle.</p>
      )}
    </Section>
  )
}

export function SourcesSection({ sources }: { sources: MapPoint['sources'] }) {
  const ok = sources.filter((source) => source.status === 'ok').length
  return (
    <details className="map-sources">
      <summary>
        Fuentes: {ok} de {sources.length} respondieron
      </summary>
      <ul>
        {sources.map((source) => (
          <li key={source.id} className={source.status === 'ok' ? '' : 'map-sources__failed'}>
            {source.status === 'ok' && <Checkmark16Regular aria-hidden="true" />}
            {sourceNames[source.id] ?? source.id}
            {source.status !== 'ok' && ' — no respondió'}
          </li>
        ))}
      </ul>
      <p>
        Datos públicos del FDOT y FDACS; se actualizan una vez al año. Confirma antes de pedir el permiso.
      </p>
    </details>
  )
}

export function OspSection({ segment }: { segment: MapSegment }) {
  const [copied, setCopied] = useState(false)
  const row = segment.ospRow
  const copyRow = async () => {
    await navigator.clipboard.writeText(ospText(segment))
    setCopied(true)
  }
  return (
    <Section icon={<DocumentText20Regular aria-hidden="true" />} title="Fila para OSP (Work Location)">
      <p className="map-note">Copia cada valor en su campo de OSP.</p>
      <dl className="map-fields">
        <Field label="County" value={row.county} copy="County" />
        <Field label="State Road ID" value={row.stateRoadId} copy="State Road ID" />
        <Field label="Section Number" value={row.sectionNumber} copy="Section Number" />
        <Field label="Beginning Milepost" value={mp(row.beginningMilepost)} copy="Beginning Milepost" />
        <Field label="Ending Milepost" value={mp(row.endingMilepost)} copy="Ending Milepost" />
      </dl>
      <Button appearance="secondary" onClick={() => void copyRow()}>
        <Copy24Regular aria-hidden="true" />
        {copied ? 'Fila copiada' : 'Copiar fila para Excel o Smartsheet'}
      </Button>
    </Section>
  )
}
