import {
  Dismiss16Regular,
  Home20Regular,
  Location20Regular,
  Road20Regular,
  Ruler20Regular,
  Search20Regular,
} from '@fluentui/react-icons'
import { useEffect, useId, useState, type KeyboardEvent } from 'react'
import { useMapSearch } from './hooks'
import { parseCoordinates, type Coordinates } from './lib/coordinates'
import type { MapSearchResult } from './types'

const icons = {
  address: Home20Regular,
  street: Road20Regular,
  milepost: Ruler20Regular,
  coordinates: Location20Regular,
}
const kinds = {
  address: 'Dirección',
  street: 'Calle',
  milepost: 'Ruta y milepost',
  coordinates: 'Coordenadas',
}
const sourceNames: Record<string, string> = {
  census_geocoder: 'direcciones (Censo)',
  fdot_streets: 'calles (FDOT)',
  fdot_milepost: 'mileposts (FDOT)',
}
const examples =
  'Prueba con una dirección (200 E Las Olas Blvd), una calle (NW 42 Ave) o una ruta con milepost (SR 953 3.5).'

export function MapSearchBox({ onSelect }: { onSelect: (point: Coordinates, label: string) => void }) {
  const [text, setText] = useState('')
  const [debounced, setDebounced] = useState('')
  const [open, setOpen] = useState(false)
  const [active, setActive] = useState(0)
  const id = useId()
  useEffect(() => {
    const timer = window.setTimeout(() => setDebounced(text), 350)
    return () => window.clearTimeout(timer)
  }, [text])
  const search = useMapSearch(debounced)
  const ready = debounced.trim().length >= 3 && text === debounced
  const results = ready ? (search.data?.results ?? []) : []
  const failed = ready ? (search.data?.sources ?? []).filter((source) => source.status !== 'ok') : []
  const showPopup = open && text.trim().length >= 3
  const choose = (result: MapSearchResult) => {
    onSelect({ lat: result.lat, lon: result.lon }, result.label)
    setText(result.label)
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
      if (typed) {
        onSelect(typed, text.trim())
        setOpen(false)
      } else if (results[active]) choose(results[active])
    } else if (event.key === 'Escape') {
      if (open) setOpen(false)
      else setText('')
    }
  }
  const status =
    !ready || search.isFetching
      ? 'Buscando…'
      : search.isError
        ? 'No se pudo buscar. Intenta de nuevo en unos segundos.'
        : results.length === 0
          ? `Sin resultados. ${examples}`
          : ''
  return (
    <div className="map-search">
      <label className="map-search__label" htmlFor={`${id}-input`}>
        Buscar lugar
      </label>
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
          placeholder="Dirección, calle, SR 953 3.5 o coordenadas"
          onChange={(event) => {
            setText(event.target.value)
            setActive(0)
            setOpen(true)
          }}
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
      {showPopup && (
        <div className="map-search__popup">
          <ul id={`${id}-list`} role="listbox" aria-label="Sugerencias">
            {results.map((result, index) => {
              const Icon = icons[result.kind]
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
                    <small>{[kinds[result.kind], result.detail].filter(Boolean).join(' · ')}</small>
                  </span>
                </li>
              )
            })}
          </ul>
          <p className="map-search__note" role="status">
            {status}
            {failed.length > 0 &&
              ` No respondió: ${failed.map((source) => sourceNames[source.id] ?? source.id).join(', ')}.`}
          </p>
        </div>
      )}
    </div>
  )
}
