import { basemapChoices, type Basemap } from '../../components/map/tileSources'
import { Button } from '../../components/ui'
import type { Coordinates } from './lib/coordinates'
import { MapSearchBox } from './MapSearchBox'

export type Mode = 'point' | 'segment'
const basemapLabels: Record<Basemap, string> = {
  streets: 'Calles (USGS)',
  satellite: 'Satélite (USGS)',
  hd: 'Satélite HD (NAIP, más zoom)',
}

type Props = {
  mode: Mode
  basemap: Basemap
  roads: boolean
  hint: string
  onMode: (mode: Mode) => void
  onBasemap: (basemap: Basemap) => void
  onRoads: (roads: boolean) => void
  onSelect: (point: Coordinates) => void
}

export function MapToolbar({ mode, basemap, roads, hint, onMode, onBasemap, onRoads, onSelect }: Props) {
  return (
    <div className="map-toolbar">
      <div className="map-toolbar__modes" role="group" aria-label="Modo de consulta">
        {(['point', 'segment'] as const).map((value) => (
          <Button
            key={value}
            appearance={mode === value ? 'primary' : 'secondary'}
            aria-pressed={mode === value}
            onClick={() => onMode(value)}
          >
            {value === 'point' ? 'Punto' : 'Tramo'}
          </Button>
        ))}
      </div>
      <MapSearchBox onSelect={onSelect} />
      <label className="map-toolbar__base">
        Mapa base
        <select value={basemap} onChange={(event) => onBasemap(event.target.value as Basemap)}>
          {basemapChoices.map((value) => (
            <option key={value} value={value}>
              {basemapLabels[value]}
            </option>
          ))}
        </select>
      </label>
      <div className="map-toolbar__layer">
        <label>
          <input type="checkbox" checked={roads} onChange={(event) => onRoads(event.target.checked)} />
          Vías del FDOT
        </label>
        {roads && (
          <span className="map-legend">
            <i className="map-legend__state" aria-hidden="true" /> estatales
            <i className="map-legend__county" aria-hidden="true" /> de condado
          </span>
        )}
      </div>
      <p className="map-toolbar__hint">{hint}</p>
    </div>
  )
}
