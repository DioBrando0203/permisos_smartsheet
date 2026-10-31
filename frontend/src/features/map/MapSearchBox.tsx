import { Dismiss16Regular, Search20Regular } from '@fluentui/react-icons'
import { useEffect, useId, useState, type KeyboardEvent } from 'react'
import type { MapScope } from './area'
import { useMapSearch } from './hooks'
import { parseCoordinates, type Coordinates } from './lib/coordinates'
import { kindIcons, kindLabels, searchExamples, searchSourceNames, searchText } from './lib/searchLabels'
import type { MapSearchResult } from './types'

/** `roadwayId`: la vía del resultado elegido (cruce, milepost o calle del FDOT), si la tiene. */
export type MapSelect = (point: Coordinates, label: string, roadwayId: string | null) => void
type Props = { scope: MapScope; onSelect: MapSelect }

export function MapSearchBox({ scope, onSelect }: Props) {
  const [text, setText] = useState('')
  const [crossing, setCrossing] = useState('')
  const [debounced, setDebounced] = useState('')
  const [open, setOpen] = useState(false)
  const [active, setActive] = useState(0)
  const id = useId()
  const wanted = searchText(text, crossing)
  useEffect(() => {
    // 500 ms: menos búsquedas a medio escribir (el Censo bloquea ráfagas de consultas).
    const timer = window.setTimeout(() => setDebounced(wanted), 500)
    return () => window.clearTimeout(timer)
  }, [wanted])
  const search = useMapSearch(debounced, scope)
  const ready = debounced.length >= 3 && wanted === debounced
  const results = ready ? (search.data?.results ?? []) : []
  const failed = ready ? (search.data?.sources ?? []).filter((source) => source.status !== 'ok') : []
  const showPopup = open && wanted.length >= 3
  const place = scope.county ? (scope.city ?? scope.county) : null
  const choose = (result: MapSearchResult) => {
    onSelect({ lat: result.lat, lon: result.lon }, result.label, result.roadwayId)
    setText(result.label)
    setCrossing('')
    setOpen(false)
  }
  const onKeyDown = (event: KeyboardEvent<HTMLInputElement>) => {
    if (event.key === 'ArrowDown' || event.key === 'ArrowUp') {
      event.preventDefault()
      setOpen(true)
      const step = event.key === 'ArrowDown' ? 1 : -1
      setActive((current) => (results.length ? (current + step + results.length) % results.length : 0))
    } else if (event.key === 'Enter') {
      event.preventDefault()
      const typed = parseCoordinates(text)
      if (typed && !crossing.trim()) {
        onSelect(typed, text.trim(), null)
        setOpen(false)
      } else if (results[active]) choose(results[active])
    } else if (event.key === 'Escape') {
      if (open) setOpen(false)
      else setText('')
    }
  }
  const typing = (update: (value: string) => void) => (value: string) => {
    update(value)
    setActive(0)
    setOpen(true)
  }
  const status =
    !ready || search.isFetching
      ? 'Buscando…'
      : search.isError
        ? 'No se pudo buscar. Intenta de nuevo en unos segundos.'
        : results.length === 0
          ? `Sin resultados${place ? ` en ${place}` : ''}. ${searchExamples}`
          : ''
  return (
    <div className="map-search">
      <label className="map-search__label" htmlFor={`${id}-input`}>
        Buscar lugar
      </label>
      <div className="map-search__fields">
        <div className="map-search__field">
          <Search20Regular aria-hidden="true" />
          <input
            id={`${id}-input`}
            role="combobox"
            aria-expanded={showPopup}
            aria-controls={`${id}-list`}
            aria-autocomplete="list"
            aria-activedescendant={showPopup && results[active] ? `${id}-${active}` : undefined}
            autoComplete="off"
            value={text}
            placeholder={
              place ? `Calle o dirección en ${place}` : 'Dirección, calle, SR 953 3.5 o coordenadas'
            }
            onChange={(event) => typing(setText)(event.target.value)}
            onFocus={() => setOpen(true)}
            onBlur={() => setOpen(false)}
            onKeyDown={onKeyDown}
          />
          {text && (
            <button type="button" aria-label="Borrar búsqueda" onClick={() => setText('')}>
              <Dismiss16Regular aria-hidden="true" />
            </button>
          )}
        </div>
        <input
          className="map-search__crossing"
          aria-label="Cruce con (opcional)"
          autoComplete="off"
          value={crossing}
          placeholder="Cruce con (opcional)"
          onChange={(event) => typing(setCrossing)(event.target.value)}
          onFocus={() => setOpen(true)}
          onBlur={() => setOpen(false)}
          onKeyDown={onKeyDown}
        />
      </div>
      {showPopup && (
        <div className="map-search__popup">
          <ul id={`${id}-list`} role="listbox" aria-label="Sugerencias">
            {results.map((result, index) => {
              const Icon = kindIcons[result.kind]
              return (
                <li
                  key={`${result.kind}-${result.label}-${result.lat}-${result.lon}`}
                  id={`${id}-${index}`}
                  role="option"
                  aria-selected={index === active}
                  onMouseDown={(event) => event.preventDefault()}
                  onMouseEnter={() => setActive(index)}
                  onClick={() => choose(result)}
                >
                  <Icon aria-hidden="true" />
                  <span>
                    <strong>{result.label}</strong>
                    <small>
                      {[kindLabels[result.kind], crossingMilepost(result), result.detail]
                        .filter(Boolean)
                        .join(' · ')}
                    </small>
                  </span>
                </li>
              )
            })}
          </ul>
          <p className="map-search__note" role="status">
            {status}
            {failed.length > 0 &&
              ` No respondió: ${failed.map((source) => searchSourceNames[source.id] ?? source.id).join(', ')}.`}
          </p>
        </div>
      )}
    </div>
  )
}

/** El milepost de un cruce sobre vía del FDOT (en `milepost` ya viene dentro del título). */
function crossingMilepost(result: MapSearchResult): string | null {
  return result.kind === 'intersection' && result.milepost !== null
    ? `MP ${result.milepost.toFixed(3)}`
    : null
}
