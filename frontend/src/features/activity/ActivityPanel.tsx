import { Info20Regular } from '@fluentui/react-icons'
import { Badge, EmptyState, Skeleton, StatTile, StatusAlert } from '../../components/ui'
import { accessLevels } from '../../lib/accessLevels'
import { errorMessage } from '../../lib/errorMessages'
import { formatRelativeTime } from '../../lib/formatters'
import type { SheetActivity } from '../../lib/sheetInsights'

type Props = {
  result?: SheetActivity
  loading: boolean
  error: Error | null
  onRetry: () => void
  onDays: (days: number) => void
}
const periods = [7, 30, 90, 365]

export function ActivityPanel({ result, loading, error, onRetry, onDays }: Props) {
  if (loading) return <ActivitySkeleton />
  if (error || !result) return <PanelError error={error} onRetry={onRetry} />
  const dominant = result.limitations[0]?.toLocaleLowerCase().includes('concentra')
  return (
    <section className="insight-panel">
      <label className="insight-select">
        Período
        <select value={result.days} onChange={(event) => onDays(Number(event.target.value))}>
          {periods.map((period) => (
            <option key={period} value={period}>
              {period} días
            </option>
          ))}
        </select>
      </label>
      <div className="insight-stats">
        <StatTile label="Filas totales" value={result.rowsTotal} />
        <StatTile label="Modificadas" value={result.changedRowsTotal} />
        <StatTile label="Editores activos" value={result.editors.length} />
        <StatTile label="Sin cambios" value={result.idleEditors.length} />
      </div>
      {result.limitations.map((item, index) => (
        <StatusAlert key={item} tone={dominant && index === 0 ? 'warning' : 'info'}>
          {item}
        </StatusAlert>
      ))}
      <ChangedRows rows={result.changedRows} />
      <Editors
        title="Editores"
        editors={result.editors.map((editor) => ({
          ...editor,
          detail: `${editor.rowsChanged} filas · ${editor.lastChange ? formatRelativeTime(editor.lastChange) : 'Sin fecha'}`,
          level: editor.accessLevel,
        }))}
      />
      <Editors
        title="Con edición sin cambios en el período"
        editors={result.idleEditors.map((editor) => ({ ...editor, detail: '', level: editor.accessLevel }))}
      />
    </section>
  )
}

function ChangedRows({ rows }: { rows: SheetActivity['changedRows'] }) {
  if (!rows.length)
    return <EmptyState icon={<Info20Regular />} title="No hubo filas modificadas en este período" />
  return (
    <section className="insight-section">
      <h2>Filas modificadas</h2>
      <table>
        <caption className="sr-only">Filas modificadas</caption>
        <thead>
          <tr>
            <th scope="col">Fila</th>
            <th scope="col">Último editor</th>
            <th scope="col">Cuándo</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.rowId}>
              <td>{row.label || `Fila ${row.rowNumber}`}</td>
              <td>{row.modifiedBy.name || row.modifiedBy.email || 'Sin dato'}</td>
              <td>{row.modifiedAt ? formatRelativeTime(row.modifiedAt) : 'Sin fecha'}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  )
}

function Editors({
  title,
  editors,
}: {
  title: string
  editors: {
    email: string | null
    name: string | null
    detail: string
    level: SheetActivity['idleEditors'][number]['accessLevel'] | null
  }[]
}) {
  if (!editors.length) return null
  return (
    <section className="insight-section">
      <h2>{title}</h2>
      <ul className="editor-list">
        {editors.map((editor) => (
          <li key={editor.email || editor.name}>
            <span>
              <strong>{editor.name || editor.email || 'Sin nombre'}</strong>
              {editor.detail && <small>{editor.detail}</small>}
            </span>
            <Badge>
              {editor.level ? accessLevels[editor.level].label : 'Ya no tiene la hoja compartida'}
            </Badge>
          </li>
        ))}
      </ul>
    </section>
  )
}

function PanelError({ error, onRetry }: { error: Error | null; onRetry: () => void }) {
  return (
    <StatusAlert tone="error" title="No se pudo cargar la actividad">
      {errorMessage('BACKEND_UNREACHABLE', error?.message).text}{' '}
      <button type="button" className="text-button" onClick={onRetry}>
        Reintentar
      </button>
    </StatusAlert>
  )
}
function ActivitySkeleton() {
  return (
    <section className="insight-panel" aria-busy="true">
      <Skeleton variant="title" />
      <div className="insight-stats">
        {Array.from({ length: 4 }, (_, index) => (
          <Skeleton key={index} variant="title" />
        ))}
      </div>
    </section>
  )
}
