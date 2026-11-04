import { Copy24Regular, Road20Regular } from '@fluentui/react-icons'
import { useState } from 'react'
import { Button, LoadingNotice, StatusAlert } from '../../components/ui'
import { permitGuide, streetTone, streetsTableText, toneClass, toneLabels } from './lib/jurisdiction'
import { MapError } from './MapResults'
import type { TraceStreet, TraceStreets } from './streets'

type Props = { result?: TraceStreets; loading: boolean; error: Error | null; onRetry: () => void }

/** Calles del condado que sigue el trazo, con su responsable y qué permiso pedir (PEN-41). */
export function TraceStreetsSection(props: Props) {
  return (
    <section className="map-result-section" aria-label="Calles y permisos del trazo">
      <h2>
        <Road20Regular aria-hidden="true" />
        Calles y permisos (condado)
      </h2>
      <Body {...props} />
    </section>
  )
}

function Body({ result, loading, error, onRetry }: Props) {
  if (loading) return <LoadingNotice>Consultando las calles del condado…</LoadingNotice>
  if (error) return <MapError error={error} onRetry={onRetry} />
  if (!result) return null
  if (!result.county)
    return <p className="map-note">Por ahora sólo St. Johns publica quién mantiene cada calle.</p>
  if (result.streets.length === 0)
    return <p className="map-note">El trazo no sigue ninguna calle del condado a menos de 30 m.</p>
  return (
    <>
      <ol className="map-streets">
        {result.streets.map((street, index) => (
          <StreetItem key={`${street.name}-${street.maintainer}-${index}`} street={street} />
        ))}
      </ol>
      {result.warnings.includes('TRACE_PARTIAL') && (
        <p className="map-note">
          Sin calle del condado: {result.unmatchedLengthMi.toFixed(3)} mi del dibujo.
        </p>
      )}
      {result.warnings.includes('STREETS_TRUNCATED') && (
        <StatusAlert tone="warning" title="Lista incompleta">
          Hay demasiadas calles cerca del trazo: puede faltar alguna.
        </StatusAlert>
      )}
      <CopyList text={streetsTableText(result.streets)} />
      <p className="map-note">
        Según el condado de {result.county} (campo MAINTENANCE). Qué permiso pedir es una guía: confírmalo con
        cada entidad.
      </p>
    </>
  )
}

function StreetItem({ street }: { street: TraceStreet }) {
  const tone = streetTone(street.authority)
  const permit = permitGuide(street.authority, street.authorityName)
  return (
    <li className="map-streets__item">
      <p className="map-streets__name">
        <i className={`map-street-chip ${toneClass(tone)}`} aria-hidden="true" />
        <strong>{street.name ?? 'Calle sin nombre'}</strong>
        <span>{street.lengthMi.toFixed(3)} mi</span>
      </p>
      <p>
        {toneLabels[tone]}: {street.authorityName ?? street.maintainer}
        {street.gated && ' · con portón'}
      </p>
      <p className="map-streets__permit">
        {permit ??
          `El condado no dice quién la mantiene («${street.maintainer}»): confírmalo antes del permiso.`}
      </p>
    </li>
  )
}

function CopyList({ text }: { text: string }) {
  const [copied, setCopied] = useState(false)
  const copy = async () => {
    await navigator.clipboard.writeText(text)
    setCopied(true)
  }
  return (
    <Button appearance="secondary" onClick={() => void copy()}>
      <Copy24Regular aria-hidden="true" />
      {copied ? 'Lista copiada' : 'Copiar lista para Excel o Smartsheet'}
    </Button>
  )
}
