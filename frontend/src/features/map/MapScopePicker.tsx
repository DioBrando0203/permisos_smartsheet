import { featuredCounties, type MapScope } from './area'
import { useMapArea, useMapCounties } from './hooks'

/** Condado y ciudad: acercan el mapa a esa zona y acotan el buscador (SPEC-11). */
export function MapScopePicker({ scope, onScope }: { scope: MapScope; onScope: (scope: MapScope) => void }) {
  const counties = useMapCounties()
  const county = useMapArea({ county: scope.county, city: null })
  // La zona guardada se conserva visible aunque la lista aún no llegue (o no haya llegado).
  const names = withSaved(
    (counties.data ?? []).map((item) => item.name),
    scope.county,
  )
  const featured = featuredCounties.filter((name) => names.includes(name))
  const others = names.filter((name) => !featured.includes(name))
  const cities = withSaved(
    (county.data?.cities ?? []).map((city) => city.name),
    scope.city,
  )
  return (
    <div className="map-scope" role="group" aria-label="Zona">
      <label className="map-toolbar__base">
        Condado
        <select
          value={scope.county ?? ''}
          onChange={(event) => onScope({ county: event.target.value || null, city: null })}
        >
          <option value="">Todo Florida</option>
          {featured.length > 0 && (
            <optgroup label="Donde trabajamos">
              {featured.map((name) => (
                <option key={name}>{name}</option>
              ))}
            </optgroup>
          )}
          {others.length > 0 && (
            <optgroup label="Otros condados">
              {others.map((name) => (
                <option key={name}>{name}</option>
              ))}
            </optgroup>
          )}
        </select>
      </label>
      <label className="map-toolbar__base">
        Ciudad
        <select
          value={scope.city ?? ''}
          disabled={!scope.county || county.isLoading}
          onChange={(event) => onScope({ county: scope.county, city: event.target.value || null })}
        >
          <option value="">
            {!scope.county ? 'Elige un condado' : county.isLoading ? 'Cargando…' : 'Todo el condado'}
          </option>
          {cities.map((name) => (
            <option key={name}>{name}</option>
          ))}
        </select>
      </label>
    </div>
  )
}

function withSaved(names: string[], saved: string | null): string[] {
  return saved && !names.includes(saved) ? [...names, saved] : names
}
