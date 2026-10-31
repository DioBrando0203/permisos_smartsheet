import { basemapChoices, type Basemap } from '../../components/map/tileSources'
import { Button } from '../../components/ui'
import type { MapScope } from './area'
import type { MapMode } from './lib/mapUrl'
import { MapScopePicker } from './MapScopePicker'
import { MapSearchBox, type MapSelect } from './MapSearchBox'

const basemapLabels: Record<Basemap, string> = {
  streets: 'Calles (USGS)',
  satellite: 'Satélite (USGS)',
  hd: 'Satélite HD (NAIP, más zoom)',
}
export type MapLayers = { roads: boolean; parcels: boolean }

type Props = {
  mode: MapMode
  scope: MapScope
  basemap: Basemap
  layers: MapLayers
  hint: string
  parcelHint: string | null
  onMode: (mode: MapMode) => void
  onScope: (scope: MapScope) => void
  onBasemap: (basemap: Basemap) => void
  onLayers: (layers: MapLayers) => void
  onSelect: MapSelect
}

export function MapToolbar({ mode, scope, basemap, layers, hint, parcelHint, ...on }: Props) {
  return (
    <div className="map-toolbar">
      <div className="map-toolbar__modes" role="group" aria-label="Modo de consulta">
        {(['point', 'trace'] as const).map((value) => (
          <Button
            key={value}
            appearance={mode === value ? 'primary' : 'secondary'}
            aria-pressed={mode === value}
            onClick={() => on.onMode(value)}
          >
            {value === 'point' ? 'Punto' : 'Trazo'}
          </Button>
        ))}
      </div>
      <MapScopePicker scope={scope} onScope={on.onScope} />
      <MapSearchBox scope={scope} onSelect={on.onSelect} />
      <label className="map-toolbar__base">
        Mapa base
        <select value={basemap} onChange={(event) => on.onBasemap(event.target.value as Basemap)}>
          {basemapChoices.map((value) => (
            <option key={value} value={value}>
              {basemapLabels[value]}
            </option>
          ))}
        </select>
      </label>
      <div className="map-toolbar__layer">
        <label>
          <input
            type="checkbox"
            checked={layers.roads}
            onChange={(event) => on.onLayers({ ...layers, roads: event.target.checked })}
          />
          Vías del FDOT
        </label>
        {layers.roads && (
          <span className="map-legend">
            <i className="map-legend__state" aria-hidden="true" /> estatales
            <i className="map-legend__county" aria-hidden="true" /> de condado
          </span>
        )}
        <label>
          <input
            type="checkbox"
            checked={layers.parcels}
            onChange={(event) => on.onLayers({ ...layers, parcels: event.target.checked })}
          />
          Límites de parcelas
        </label>
        {parcelHint && (
          <span className="map-legend" role="status">
            {parcelHint}
          </span>
        )}
      </div>
      <p className="map-toolbar__hint">{hint}</p>
    </div>
  )
}
