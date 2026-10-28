import { useState } from 'react'
import { Button, ConfirmDialog } from '../../components/ui'
import { accessLevels } from '../../lib/accessLevels'
import type { AccessLevel, LockedReason } from '../../lib/types'
import type { GroupedShare } from './lib/groupShares'

type Props = {
  share: GroupedShare
  sheetName: string
  readOnly: boolean
  pending: boolean
  onUpdate: (id: string, level: Exclude<AccessLevel, 'OWNER'>) => void
  onRemove: (id: string) => void
}
const readOnlyReason = 'Modo solo lectura: el panel no cambia nada en Smartsheet'
const levels = (Object.keys(accessLevels) as AccessLevel[]).filter((level) => level !== 'OWNER')

export function ShareActions({ share, sheetName, readOnly, pending, onUpdate, onRemove }: Props) {
  const [nextLevel, setNextLevel] = useState<Exclude<AccessLevel, 'OWNER'> | null>(null)
  const [removing, setRemoving] = useState(false)
  const reason = lockedMessage(share.lockedReason) ?? (readOnly ? readOnlyReason : null)
  const disabled = Boolean(reason) || !share.editable || pending
  const requestLevel = (level: Exclude<AccessLevel, 'OWNER'>) => {
    if (level === share.accessLevel) return
    const needsConfirm = accessLevels[level].rank < accessLevels[share.accessLevel].rank || level === 'ADMIN'
    if (needsConfirm) setNextLevel(level)
    else onUpdate(share.id, level)
  }
  if (disabled)
    return (
      <span className="locked-action">
        <Button appearance="subtle" size="sm" disabled title={reason ?? 'No se puede cambiar este acceso'}>
          Cambiar nivel
        </Button>
        <span>{reason ?? 'No se puede cambiar este acceso'}</span>
      </span>
    )
  return (
    <span className="share-actions">
      <label className="sr-only" htmlFor={`level-${share.id}`}>
        Nivel de acceso
      </label>
      <select
        id={`level-${share.id}`}
        value={share.accessLevel}
        onChange={(event) => requestLevel(event.target.value as Exclude<AccessLevel, 'OWNER'>)}
        disabled={pending}
      >
        {levels.map((level) => (
          <option key={level} value={level}>
            {accessLevels[level].label}
          </option>
        ))}
      </select>
      <Button
        appearance="subtle"
        size="sm"
        disabled={pending}
        onClick={() => setRemoving(true)}
        aria-label={`Quitar acceso a ${share.name || share.email || 'persona'}`}
      >
        Quitar
      </Button>
      <ConfirmDialog
        open={nextLevel !== null}
        title="¿Cambiar nivel de acceso?"
        confirmLabel="Cambiar nivel"
        onClose={() => setNextLevel(null)}
        onConfirm={() => {
          if (nextLevel) onUpdate(share.id, nextLevel)
          setNextLevel(null)
        }}
      >{`Se cambiará de ${accessLevels[share.accessLevel].label} a ${nextLevel ? accessLevels[nextLevel].label : ''} en ${sheetName}.`}</ConfirmDialog>
      <ConfirmDialog
        open={removing}
        title="¿Quitar acceso?"
        confirmLabel="Quitar acceso"
        onClose={() => setRemoving(false)}
        onConfirm={() => {
          onRemove(share.id)
          setRemoving(false)
        }}
      >{`Esta persona dejará de tener acceso a ${sheetName}. Puede volver a darle acceso después.`}</ConfirmDialog>
    </span>
  )
}

function lockedMessage(reason: LockedReason): string | null {
  if (reason === 'OWNER') return 'Propietario de la hoja'
  if (reason === 'INHERITED') return 'Heredado del workspace: cámbielo en el workspace'
  if (reason === 'NO_PERMISSION') return 'La cuenta del panel no puede administrar esta hoja'
  return null
}
