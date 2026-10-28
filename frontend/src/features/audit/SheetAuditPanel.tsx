import { Link } from 'react-router'
import { Info20Regular } from '@fluentui/react-icons'
import { Badge, EmptyState, MeterBar, Skeleton, StatTile, StatusAlert } from '../../components/ui'
import { errorMessage } from '../../lib/errorMessages'
import { personPath } from '../../lib/routes'
import { severity } from '../../lib/severity'
import type { SheetAudit } from '../../lib/sheetInsights'

type Props = { result?: SheetAudit; loading: boolean; error: Error | null; onRetry: () => void }

export function SheetAuditPanel({ result, loading, error, onRetry }: Props) {
  if (loading) return <AuditSkeleton />
  if (error || !result)
    return <PanelError title="No se pudo cargar la auditoría" error={error} onRetry={onRetry} />
  return (
    <section className="insight-panel">
      <div className="insight-stats">
        <StatTile label="Accesos" value={result.total} />
        <StatTile
          label="Externos"
          value={result.orgKnown ? (result.externalCount ?? 0) : 'No se pudo saber'}
        />
        <StatTile label="Sin nombre" value={result.unnamedCount} />
        <StatTile label="Fuera de contactos" value={result.notInContactsCount} />
      </div>
      {!result.orgKnown && (
        <StatusAlert tone="info">No se pudo identificar la organización de la cuenta.</StatusAlert>
      )}
      {result.alerts.length ? (
        <AlertList audit={result} />
      ) : (
        <EmptyState icon={<Info20Regular />} title="Sin alertas en esta hoja" />
      )}
      <div className="insight-grid">
        <Meters title="Por nivel" values={result.byLevel} />
        <Meters title="Por origen" values={result.byScope} />
      </div>
      {result.byDomain.length > 0 && (
        <section className="insight-section">
          <h2>Por dominio</h2>
          <ul className="domain-list">
            {result.byDomain.map((domain) => (
              <li key={domain.domain}>
                <span>{domain.domain}</span>
                <span>{domain.count}</span>
                {domain.isPersonal && <Badge>Personal</Badge>}
              </li>
            ))}
          </ul>
        </section>
      )}
    </section>
  )
}

function AlertList({ audit }: { audit: SheetAudit }) {
  return (
    <section className="insight-section">
      <h2>Alertas</h2>
      {audit.alerts.map((alert) => (
        <article className="audit-alert" key={alert.code}>
          <header>
            <Badge tone={severity[alert.severity].tone}>{severity[alert.severity].label}</Badge>
            <strong>{alert.message}</strong>
            <span>{alert.count}</span>
          </header>
          <ul>
            {alert.people.map((person) => (
              <li key={person.key}>
                <Link to={personPath(person.key)}>{person.name || person.email || 'Sin nombre'}</Link>
                <span>{person.accessLevel}</span>
              </li>
            ))}
          </ul>
        </article>
      ))}
    </section>
  )
}

function Meters({ title, values }: { title: string; values: Record<string, number> }) {
  const max = Math.max(0, ...Object.values(values))
  return (
    <section className="insight-section">
      <h2>{title}</h2>
      {Object.entries(values).map(([label, value]) => (
        <MeterBar key={label} label={label} value={value} max={max} />
      ))}
    </section>
  )
}

function PanelError({ title, error, onRetry }: { title: string; error: Error | null; onRetry: () => void }) {
  return (
    <StatusAlert tone="error" title={title}>
      {errorMessage('BACKEND_UNREACHABLE', error?.message).text}{' '}
      <button type="button" className="text-button" onClick={onRetry}>
        Reintentar
      </button>
    </StatusAlert>
  )
}

function AuditSkeleton() {
  return (
    <section className="insight-panel" aria-busy="true">
      <div className="insight-stats">
        {Array.from({ length: 4 }, (_, index) => (
          <Skeleton key={index} variant="title" />
        ))}
      </div>
      <Skeleton variant="title" />
      <Skeleton variant="line" />
    </section>
  )
}
