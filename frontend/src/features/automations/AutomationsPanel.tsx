import { Badge, EmptyState, Skeleton, StatTile, StatusAlert } from '../../components/ui'
import { Info20Regular } from '@fluentui/react-icons'
import { errorMessage } from '../../lib/errorMessages'
import type { Automation, SheetAutomations } from '../../lib/sheetInsights'

type Props = { result?: SheetAutomations; loading: boolean; error: Error | null; onRetry: () => void }
const labels = { ok: 'Funcionan', with_problems: 'Con problemas', disabled: 'Apagadas' }

export function AutomationsPanel({ result, loading, error, onRetry }: Props) {
  if (loading) return <AutomationSkeleton />
  if (error || !result) return <PanelError error={error} onRetry={onRetry} />
  return (
    <section className="insight-panel">
      <div className="insight-stats">
        {Object.entries(labels).map(([status, label]) => (
          <StatTile key={status} label={label} value={result.counts[status] ?? 0} />
        ))}
      </div>
      <p className="automation-note">
        Para corregirlas, ábralas en Smartsheet: Automatización &gt; Administrar flujos de trabajo.
      </p>
      {result.automations.length ? (
        <div className="automation-list">
          {result.automations.map((automation) => (
            <AutomationCard key={automation.id} automation={automation} />
          ))}
        </div>
      ) : (
        <EmptyState icon={<Info20Regular />} title="Esta hoja no tiene automatizaciones" />
      )}
    </section>
  )
}

function AutomationCard({ automation }: { automation: Automation }) {
  const tone =
    automation.status === 'ok' ? 'info' : automation.status === 'with_problems' ? 'warning' : 'neutral'
  return (
    <article className="automation-card">
      <header>
        <div>
          <h2>{automation.name}</h2>
          <p>
            {automation.actionType || 'Tipo no disponible'} ·{' '}
            {automation.frequency || 'Frecuencia no disponible'}
          </p>
        </div>
        <Badge tone={tone}>{labels[automation.status]}</Badge>
      </header>
      <p>
        <strong>Avisa a: </strong>
        {automation.notifyAllShared
          ? 'Todas las personas con acceso'
          : automation.recipientEmails.join(', ') || 'Sin destinatarios por correo'}
      </p>
      {automation.recipientColumns.length > 0 && (
        <ul>
          {automation.recipientColumns.map((column) => (
            <li key={column.id}>
              {column.title} ({column.type}){' '}
              {!column.isContact && <Badge tone="warning">No es columna de contacto</Badge>}
            </li>
          ))}
        </ul>
      )}
      {automation.smartsheetReason && (
        <p>
          <strong>Motivo de Smartsheet: </strong>
          {automation.smartsheetReason}
        </p>
      )}
      {automation.problems.map((problem) => (
        <StatusAlert key={problem.code} tone="warning">
          {problem.message}
        </StatusAlert>
      ))}
    </article>
  )
}

function PanelError({ error, onRetry }: { error: Error | null; onRetry: () => void }) {
  return (
    <StatusAlert tone="error" title="No se pudieron cargar las automatizaciones">
      {errorMessage('BACKEND_UNREACHABLE', error?.message).text}{' '}
      <button type="button" className="text-button" onClick={onRetry}>
        Reintentar
      </button>
    </StatusAlert>
  )
}
function AutomationSkeleton() {
  return (
    <section className="insight-panel" aria-busy="true">
      <div className="insight-stats">
        {Array.from({ length: 3 }, (_, index) => (
          <Skeleton key={index} variant="title" />
        ))}
      </div>
      <Skeleton variant="line" />
    </section>
  )
}
