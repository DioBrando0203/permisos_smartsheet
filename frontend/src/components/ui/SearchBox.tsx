import { Dismiss16Regular, Search20Regular } from '@fluentui/react-icons'
import { useEffect, useRef } from 'react'

type Props = {
  value: string
  onChange: (value: string) => void
  placeholder: string
  label: string
  shortcut?: string
}

function isTyping(target: EventTarget | null): boolean {
  return (
    target instanceof HTMLElement &&
    (target.isContentEditable || ['INPUT', 'TEXTAREA', 'SELECT'].includes(target.tagName))
  )
}

export function SearchBox({ value, onChange, placeholder, label, shortcut }: Props) {
  const input = useRef<HTMLInputElement>(null)
  useEffect(() => {
    if (!shortcut) return
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key !== shortcut || event.ctrlKey || event.metaKey || event.altKey || isTyping(event.target))
        return
      event.preventDefault()
      input.current?.focus()
    }
    window.addEventListener('keydown', onKeyDown)
    return () => window.removeEventListener('keydown', onKeyDown)
  }, [shortcut])

  return (
    <div className="search-box" role="search">
      <Search20Regular className="search-box__icon" aria-hidden="true" />
      <input
        ref={input}
        type="search"
        value={value}
        placeholder={placeholder}
        aria-label={label}
        aria-keyshortcuts={shortcut}
        onChange={(event) => onChange(event.target.value)}
        onKeyDown={(event) => {
          if (event.key === 'Escape' && value) {
            event.preventDefault()
            onChange('')
          }
        }}
      />
      {value && <ButtonClear onClick={() => onChange('')} />}
    </div>
  )
}

function ButtonClear({ onClick }: { onClick: () => void }) {
  return (
    <button type="button" className="search-box__clear" aria-label="Borrar búsqueda" onClick={onClick}>
      <Dismiss16Regular aria-hidden="true" />
    </button>
  )
}
