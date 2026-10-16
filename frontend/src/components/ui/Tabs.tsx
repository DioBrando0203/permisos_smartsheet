import type { KeyboardEvent } from 'react'

export type TabItem = { id: string; label: string }
type Props = {
  label: string
  tabs: TabItem[]
  selected: string
  onSelect: (id: string) => void
  panelId: string
}

export function Tabs({ label, tabs, selected, onSelect, panelId }: Props) {
  const move = (index: number) => {
    const tab = tabs[(index + tabs.length) % tabs.length]
    onSelect(tab.id)
    document.getElementById(`${panelId}-${tab.id}`)?.focus()
  }
  const onKeyDown = (event: KeyboardEvent<HTMLButtonElement>, index: number) => {
    const targets: Record<string, number> = {
      ArrowRight: index + 1,
      ArrowLeft: index - 1,
      Home: 0,
      End: tabs.length - 1,
    }
    if (event.key in targets) {
      event.preventDefault()
      move(targets[event.key])
    }
  }
  return (
    <div className="tabs" role="tablist" aria-label={label}>
      {tabs.map((tab, index) => (
        <button
          key={tab.id}
          id={`${panelId}-${tab.id}`}
          type="button"
          role="tab"
          className="tabs__tab"
          aria-selected={tab.id === selected}
          aria-controls={panelId}
          tabIndex={tab.id === selected ? 0 : -1}
          onClick={() => onSelect(tab.id)}
          onKeyDown={(event) => onKeyDown(event, index)}
        >
          {tab.label}
        </button>
      ))}
    </div>
  )
}
