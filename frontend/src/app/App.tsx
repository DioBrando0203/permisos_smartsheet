import { Outlet } from 'react-router'
import { AppLayout } from '../components/layout/AppLayout'
import { Button, Spinner, StatusAlert } from '../components/ui'
import { ApiError } from '../lib/api'
import { errorMessage } from '../lib/errorMessages'
import { useHealth, useMe } from '../features/shell/hooks'

export function App() {
  const health = useHealth()
  const me = useMe()
  const retry = () => {
    void health.refetch()
    void me.refetch()
  }
  const error = health.error ?? me.error
  if (error || !health.data) return <GlobalError error={error} onRetry={retry} />
  if (health.data.smartsheet === 'missing_token') return <GlobalError code="TOKEN_MISSING" onRetry={retry} />
  return (
    <AppLayout me={me.data ?? null} readOnly={health.data.readOnly}>
      {me.isLoading ? (
        <div className="shell-loading">
          <Spinner label="Cargando la cuenta" />
        </div>
      ) : (
        <Outlet context={{ me: me.data ?? null, readOnly: health.data.readOnly }} />
      )}
    </AppLayout>
  )
}

function GlobalError({ error, code, onRetry }: { error?: Error | null; code?: string; onRetry: () => void }) {
  const apiError = error instanceof ApiError ? error : null
  const message = errorMessage(code ?? apiError?.code ?? 'BACKEND_UNREACHABLE', apiError?.message)
  return (
    <main className="global-error">
      <StatusAlert tone="error" title="No se pudo iniciar el panel">
        <p>{message.text}</p>
        {message.action && <p>{message.action}</p>}
        <Button appearance="secondary" onClick={onRetry}>
          Reintentar
        </Button>
      </StatusAlert>
    </main>
  )
}
