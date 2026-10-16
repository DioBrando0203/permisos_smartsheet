import { LockClosed16Regular } from '@fluentui/react-icons'
import { EmptyState, Spinner, StatusAlert } from '../components/ui'
import { ApiError } from '../lib/api'
import { errorMessage } from '../lib/errorMessages'
import { useHealth, useMe } from '../features/shell/hooks'

export function App() {
  const health = useHealth()
  const me = useMe()
  if (health.isLoading || me.isLoading)
    return (
      <main className="startup">
        <Spinner label="Cargando el panel" />
      </main>
    )
  if (health.error || me.error || !health.data || !me.data) {
    const failure = health.error ?? me.error
    const text =
      failure instanceof ApiError
        ? errorMessage(failure.code, failure.message).text
        : failure instanceof Error
          ? errorMessage('BACKEND_UNREACHABLE', failure.message).text
          : 'Algo salió mal.'
    return (
      <main className="startup">
        <StatusAlert tone="error" title="No se pudo iniciar el panel">
          {text}
        </StatusAlert>
      </main>
    )
  }
  return (
    <main className="startup">
      <header className="startup__header">
        <h1>Permisos de hojas</h1>
        <span>{me.data.name || me.data.email}</span>
      </header>
      {health.data.readOnly && (
        <div className="startup__banner">
          <LockClosed16Regular aria-hidden="true" />
          Modo solo lectura: el panel no cambia nada en Smartsheet
        </div>
      )}
      <EmptyState icon={<LockClosed16Regular />} title="El panel está listo">
        <p>Las vistas de hojas y permisos se incorporarán en la siguiente fase.</p>
      </EmptyState>
    </main>
  )
}
