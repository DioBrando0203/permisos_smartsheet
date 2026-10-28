import { PersonAdd20Regular } from '@fluentui/react-icons'
import { useState } from 'react'
import { Avatar, Badge, Button, EmptyState, Skeleton, StatusAlert, Toast } from '../../components/ui'
import { accessLevels } from '../../lib/accessLevels'
import { errorMessage } from '../../lib/errorMessages'
import type { ShareList, Sheet } from '../../lib/types'
import { displayName, groupShares } from './lib/groupShares'
import { ShareDialog } from './ShareDialog'
import { ShareActions } from './ShareActions'
import { useShareMutations } from './mutations'

type Props = {
  sheet: Sheet
  result?: ShareList
  loading: boolean
  error: Error | null
  tokenEmail: string | null
  readOnly: boolean
  onRetry: () => void
}
const readOnlyReason = 'Modo solo lectura: el panel no cambia nada en Smartsheet'

export function ShareTable({ sheet, result, loading, error, tokenEmail, readOnly, onRetry }: Props) {
  const [shareOpen, setShareOpen] = useState(false)
  const [toast, setToast] = useState<string | null>(null)
  const mutations = useShareMutations(sheet.id)
  if (loading) return <ShareTableSkeleton />
  if (error || !result)
    return (
      <StatusAlert tone="error" title="No se pudieron cargar los permisos">
        {errorMessage('BACKEND_UNREACHABLE', error?.message).text}{' '}
        <Button appearance="subtle" onClick={onRetry}>
          Reintentar
        </Button>
      </StatusAlert>
    )
  const shares = groupShares(result.shares)
  const canShare = sheet.inMyList && sheet.canManageShares
  return (
    <section className="share-table">
      <header className="share-table__header">
        <div>
          <h2>Personas con la hoja compartida</h2>
          {sheet.hasDynamicView && (
            <p>Puede haber personas que la ven por una vista dinámica y no aparecen aquí.</p>
          )}
        </div>
        {canShare && (
          <div className="share-table__write">
            <Button
              disabled={readOnly}
              title={readOnly ? readOnlyReason : undefined}
              onClick={() => setShareOpen(true)}
            >
              <PersonAdd20Regular aria-hidden="true" />
              Compartir
            </Button>
            {readOnly && <span>{readOnlyReason}</span>}
          </div>
        )}
      </header>
      {!sheet.inMyList && (
        <StatusAlert tone="info" title="Sólo consulta">
          La hoja es de {sheet.ownerEmail || 'otra persona'} y no está compartida con la cuenta del panel.
        </StatusAlert>
      )}
      {shares.length ? (
        <table>
          <caption className="sr-only">Personas con la hoja compartida: {sheet.name}</caption>
          <thead>
            <tr>
              <th scope="col">Persona</th>
              <th scope="col">Nivel</th>
              <th scope="col">Origen</th>
              <th scope="col">Acciones</th>
            </tr>
          </thead>
          <tbody>
            {shares.map((share) => (
              <tr key={`${share.id}-${share.scopes.join('-')}`}>
                <td data-label="Persona">
                  <div className="share-person">
                    <Avatar name={displayName(share)} />
                    <span>
                      <strong>
                        {displayName(share)}
                        {share.email === tokenEmail && ' (usted)'}
                      </strong>
                      {share.email && <small>{share.email}</small>}
                      {share.type === 'GROUP' && <small>Grupo</small>}
                    </span>
                  </div>
                </td>
                <td data-label="Nivel">
                  <Badge>{accessLevels[share.accessLevel].label}</Badge>
                </td>
                <td data-label="Origen">
                  {share.scopes.map((scope) => (
                    <span key={scope}>{scope === 'WORKSPACE' ? 'Heredado del workspace' : 'Propio'} </span>
                  ))}
                </td>
                <td data-label="Acciones">
                  <ShareActions
                    share={share}
                    sheetName={sheet.name}
                    readOnly={readOnly}
                    pending={mutations.update.isPending || mutations.remove.isPending}
                    onUpdate={(shareId, accessLevel) => mutations.update.mutate({ shareId, accessLevel })}
                    onRemove={(shareId) => mutations.remove.mutate(shareId)}
                  />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : (
        <EmptyState
          icon={<PersonAdd20Regular />}
          title="Sólo la cuenta del panel tiene esta hoja compartida"
          actions={
            canShare ? (
              <Button
                disabled={readOnly}
                title={readOnly ? readOnlyReason : undefined}
                onClick={() => setShareOpen(true)}
              >
                Compartir
              </Button>
            ) : undefined
          }
        />
      )}
      <ShareDialog
        open={shareOpen}
        sheetName={sheet.name}
        pending={mutations.create.isPending}
        error={mutations.create.error}
        onClose={() => setShareOpen(false)}
        onCreate={(input) =>
          mutations.create.mutate(input, {
            onSuccess: (result) => {
              setShareOpen(false)
              setToast(`Se dio acceso a ${result.created.length} personas en ${sheet.name}.`)
            },
          })
        }
      />
      {toast && <Toast onClose={() => setToast(null)}>{toast}</Toast>}
    </section>
  )
}

function ShareTableSkeleton() {
  return (
    <section className="share-table" aria-busy="true">
      <h2>Personas con la hoja compartida</h2>
      {Array.from({ length: 6 }, (_, index) => (
        <div className="share-table__skeleton" key={index}>
          <Skeleton variant="avatar" />
          <Skeleton />
          <Skeleton />
        </div>
      ))}
    </section>
  )
}
