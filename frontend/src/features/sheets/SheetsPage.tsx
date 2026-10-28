import { useEffect } from 'react'
import { useNavigate, useParams, useSearchParams } from 'react-router'
import { StatusAlert } from '../../components/ui'
import { errorMessage } from '../../lib/errorMessages'
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
            onRefresh={refresh}
            onTab={(value) => updateParams({ tab: value === 'permisos' ? '' : value })}
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
  onRefresh,
  onTab,
  shares,
  tokenEmail,
  readOnly,
}: {
  sheet: ReturnType<typeof useSheet>['data']
  loading: boolean
  error: Error | null
  tab: string
  onRefresh: () => void
  onTab: (tab: string) => void
  shares: ReturnType<typeof useShares>
  tokenEmail: string | null
  readOnly: boolean
}) {
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

function Welcome() {
  return (
    <section className="sheet-welcome">
      <h1>Seleccione una hoja</h1>
      <p>Elija una hoja de la lista para ver quién tiene la hoja compartida y con qué nivel.</p>
    </section>
  )
}
