import { Person24Regular } from '@fluentui/react-icons'
import { useState } from 'react'
import { Link } from 'react-router'
import { Avatar, Badge, Button, EmptyState, Skeleton, StatusAlert } from '../../components/ui'
import { accessLevels } from '../../lib/accessLevels'
import { errorMessage } from '../../lib/errorMessages'
import { formatRelativeTime } from '../../lib/formatters'
import { sheetPath } from '../../lib/routes'
import type { PersonDetail as PersonDetailData } from '../../lib/types'
import { RevokeDialog } from './RevokeDialog'
import { useRevokePerson } from './revoke'

type Props = {
  loading: boolean
  error: Error | null
  detail?: PersonDetailData
  readOnly: boolean
  onRetry: () => void
}

export function PersonDetail({ loading, error, detail, readOnly, onRetry }: Props) {
  const [revokeOpen, setRevokeOpen] = useState(false)
  const revoke = useRevokePerson(detail?.person.key ?? '')
  if (loading)
    return (
      <section className="person-detail" aria-busy="true">
        <Skeleton variant="title" />
      </section>
    )
  if (error || !detail)
    return (
      <StatusAlert tone="error" title="No se pudo cargar la persona">
        {errorMessage('PERSON_NOT_FOUND', error?.message).text}{' '}
        <Button appearance="subtle" onClick={onRetry}>
          Reintentar
        </Button>
      </StatusAlert>
    )
  const name = detail.person.name || detail.person.email || 'Sin nombre'
  return (
    <section className="person-detail">
      <header>
        <Avatar name={name} />
        <div>
          <h1>
            {name}
            {detail.person.isTokenOwner && ' (usted)'}
          </h1>
          {detail.person.email && <p>{detail.person.email}</p>}
          <p>
            {detail.person.isOrgMember ? 'Organización' : 'Externo'}
            {detail.person.isContact && ' · Contacto'}
            {detail.person.lastLogin && ` · Última conexión ${formatRelativeTime(detail.person.lastLogin)}`}
          </p>
          <p>
            {detail.person.sheetCount} hojas
            {detail.person.highestLevel &&
              ` · nivel más alto: ${accessLevels[detail.person.highestLevel].label}`}
          </p>
        </div>
      </header>
      <div className="person-detail__actions">
        <Button onClick={() => setRevokeOpen(true)}>Quitar de varias hojas</Button>
        {readOnly && (
          <span>La simulación funciona; aplicar cambios está bloqueado por el modo solo lectura.</span>
        )}
      </div>
      <h2>Hojas con acceso</h2>
      {detail.sheets.length ? (
        <table>
          <caption className="sr-only">Hojas con acceso de {name}</caption>
          <thead>
            <tr>
              <th scope="col">Hoja</th>
              <th scope="col">Nivel</th>
              <th scope="col">Origen</th>
              <th scope="col">Acciones</th>
            </tr>
          </thead>
          <tbody>
            {detail.sheets.map((sheet) => (
              <tr key={`${sheet.sheetId}-${sheet.shareId}-${sheet.scope}`}>
                <td>
                  <Link to={sheetPath(sheet.sheetId)}>{sheet.sheetName}</Link>
                </td>
                <td>
                  <Badge>{accessLevels[sheet.accessLevel].label}</Badge>
                </td>
                <td>{sheet.scope === 'WORKSPACE' ? 'Heredado del workspace' : 'Propio'}</td>
                <td>
                  <Button
                    appearance="subtle"
                    size="sm"
                    disabled
                    title="Modo solo lectura: el panel no cambia nada en Smartsheet"
                  >
                    Quitar acceso
                  </Button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : (
        <EmptyState icon={<Person24Regular />} title="Esta persona no tiene acceso a hojas" />
      )}
      {revokeOpen && (
        <RevokeDialog
          open
          detail={detail}
          readOnly={readOnly}
          plan={revoke.simulate.data}
          pending={revoke.simulate.isPending}
          error={revoke.simulate.error}
          onClose={() => setRevokeOpen(false)}
          onSimulate={(sheetIds) => revoke.simulate.mutate(sheetIds)}
        />
      )}
    </section>
  )
}
