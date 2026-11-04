import { toneClass, toneLabels, type StreetTone } from './lib/jurisdiction'

/** Leyenda de "Jurisdicción de calles": cada color dice con texto quién mantiene la calle. */
export function StreetLegend({ tones }: { tones: StreetTone[] }) {
  if (tones.length === 0) return null
  return (
    <span className="map-legend map-legend--streets" aria-label="Colores de las calles">
      {tones.map((tone) => (
        <span key={tone} className="map-legend__item">
          <i className={`map-street-chip ${toneClass(tone)}`} aria-hidden="true" />
          {toneLabels[tone]}
        </span>
      ))}
    </span>
  )
}
