import { useEffect } from 'react'
import { useNavigate, useParams, useSearchParams } from 'react-router'
import { StatusAlert } from '../../components/ui'
import { errorMessage } from '../../lib/errorMessages'
import { ActivityPanel } from '../activity/ActivityPanel'
import { useSheetActivity } from '../activity/hooks'
import { SheetAuditPanel } from '../audit/SheetAuditPanel'
import { useSheetAudit } from '../audit/hooks'
import { AutomationsPanel } from '../automations/AutomationsPanel'
import { useSheetAutomations } from '../automations/hooks'
import { sheetPath } from '../../lib/routes'
import { useShares } from '../shares/hooks'
import { ShareTable } from '../shares/ShareTable'
import { useShellContext } from '../shell/ShellContext'
import { useSheet, useSheets } from './hooks'
import { SheetHeader } from './SheetHeader'
import { SheetList, type SheetScope } from './SheetList'
import { SheetTabs } from './SheetTabs'

export function SheetsPage() {
  const { sheetId } = useParams()
  const [params, setParams] = useSearchParams()
  const navigate = useNavigate()
  const { me, readOnly } = useShellContext()
  const sheets = useSheets()
  const sheet = useSheet(sheetId ?? '')
  const shares = useShares(sheet.data?.id ?? sheetId ?? '')
  const scope = (params.get('scope') as SheetScope | null) ?? 'all'
  const query = params.get('q') ?? ''
  const tab = params.get('tab') ?? 'permisos'
  const days = Number(params.get('days') ?? '30')
  useEffect(() => {
    if (sheetId && sheet.data?.id && sheetId !== sheet.data.id)
      navigate(sheetPath(sheet.data.id, tab), { replace: true })
  }, [navigate, sheet.data?.id, sheetId, tab])
  const updateParams = (values: Record<string, string>) => {
    const next = new URLSearchParams(params)
    Object.entries(values).forEach(([key, value]) => (value ? next.set(key, value) : next.delete(key)))
    setParams(next)
  }
  const refresh = () => {
    void sheets.refetch()
    void sheet.refetch()
    void shares.refetch()
  }
  return (
    <div className="sheets-page">
      <aside className="sheets-page__list">
        <SheetList
          result={sheets.data}
          loading={sheets.isLoading}
          error={sheets.error}
          scope={scope}
          query={query}
          selectedId={sheet.data?.id ?? sheetId}
          onScope={(value) => updateParams({ scope: value === 'all' ? '' : value })}
          onQuery={(value) => updateParams({ q: value })}
          onRefresh={() => void sheets.refetch()}
        />
      </aside>
      <section className="sheets-page__detail">
        {sheetId ? (
          <SheetDetail
            loading={sheet.isLoading}
            error={sheet.error}
            sheet={sheet.data}
            tab={tab}
            days={periods.includes(days) ? days : 30}
            onRefresh={refresh}
            onTab={(value) => updateParams({ tab: value === 'permisos' ? '' : value })}
            onDays={(value) => updateParams({ days: value === 30 ? '' : String(value) })}
            shares={shares}
            tokenEmail={me?.email ?? null}
            readOnly={readOnly}
          />
        ) : (
          <Welcome />
        )}
      </section>
    </div>
  )
}

function SheetDetail({
  sheet,
  loading,
  error,
  tab,
  days,
  onRefresh,
  onTab,
  onDays,
  shares,
  tokenEmail,
  readOnly,
}: {
  sheet: ReturnType<typeof useSheet>['data']
  loading: boolean
  error: Error | null
  tab: string
  days: number
  onRefresh: () => void
  onTab: (tab: string) => void
  onDays: (days: number) => void
  shares: ReturnType<typeof useShares>
  tokenEmail: string | null
  readOnly: boolean
}) {
  const id = sheet?.id ?? ''
  const audit = useSheetAudit(tab === 'auditoria' ? id : '')
  const activity = useSheetActivity(tab === 'actividad' ? id : '', days)
  const automations = useSheetAutomations(tab === 'automatizaciones' ? id : '')
  if (error)
    return (
      <StatusAlert tone="error" title="No se pudo cargar la hoja">
        {errorMessage('SHEET_NOT_FOUND', error.message).text}
      </StatusAlert>
    )
  return (
    <>
      {<SheetHeader sheet={sheet} loading={loading} onRefresh={onRefresh} />}{' '}
      {sheet && (
        <>
          <SheetTabs selected={tab} onSelect={onTab} />
          <div id="sheet-panel" role="tabpanel">
            {tab === 'permisos' ? (
              <ShareTable
                sheet={sheet}
                result={shares.data}
                loading={shares.isLoading}
                error={shares.error}
                tokenEmail={tokenEmail}
                readOnly={readOnly}
                onRetry={() => void shares.refetch()}
              />
            ) : tab === 'auditoria' ? (
              <SheetAuditPanel
                result={audit.data}
                loading={audit.isLoading}
                error={audit.error}
                onRetry={() => void audit.refetch()}
              />
            ) : tab === 'actividad' ? (
              <ActivityPanel
                result={activity.data}
                loading={activity.isLoading}
                error={activity.error}
                onRetry={() => void activity.refetch()}
                onDays={onDays}
              />
            ) : tab === 'automatizaciones' ? (
              <AutomationsPanel
                result={automations.data}
                loading={automations.isLoading}
                error={automations.error}
                onRetry={() => void automations.refetch()}
              />
            ) : (
              <StatusAlert tone="info" title="Próximamente">
                Esta pestaña se incorpora en F3.
              </StatusAlert>
            )}
          </div>
        </>
      )}
    </>
  )
}

const periods = [7, 30, 90, 365]

function Welcome() {
  return (
    <section className="sheet-welcome">
      <h1>Seleccione una hoja</h1>
      <p>Elija una hoja de la lista para ver quién tiene la hoja compartida y con qué nivel.</p>
    </section>
  )
}
