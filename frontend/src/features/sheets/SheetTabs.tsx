import { Tabs } from '../../components/ui'

const tabs = [
  { id: 'permisos', label: 'Permisos' },
  { id: 'auditoria', label: 'Auditoría' },
  { id: 'actividad', label: 'Actividad' },
  { id: 'automatizaciones', label: 'Automatizaciones' },
  { id: 'calidad', label: 'Calidad de datos' },
]

export function SheetTabs({ selected, onSelect }: { selected: string; onSelect: (tab: string) => void }) {
  return (
    <Tabs
      label="Detalle de hoja"
      tabs={tabs}
      selected={tabs.some((tab) => tab.id === selected) ? selected : 'permisos'}
      onSelect={onSelect}
      panelId="sheet-panel"
    />
  )
}
