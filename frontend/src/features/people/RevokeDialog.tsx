import { useState } from 'react'
import { Button, Dialog, StatusAlert } from '../../components/ui'
import type { PersonDetail } from '../../lib/types'
import type { RevokePlan } from './revoke'

type Props = {
  open: boolean
  detail: PersonDetail
  readOnly: boolean
  plan?: RevokePlan
  pending: boolean
  error: Error | null
  onClose: () => void
  onSimulate: (sheetIds: string[] | null) => void
}
const blocked = (reason: string | null) =>
  reason === 'OWNER'
    ? 'Propietario de la hoja'
    : reason === 'INHERITED'
      ? 'Heredado del workspace'
      : reason === 'NO_PERMISSION'
        ? 'La cuenta del panel no puede administrar esta hoja'
        : null

export function RevokeDialog({ open, detail, readOnly, plan, pending, error, onClose, onSimulate }: Props) {
  const editable = detail.sheets.filter((sheet) => sheet.editable && !blocked(sheet.lockedReason))
  const [selected, setSelected] = useState<string[]>(editable.map((sheet) => sheet.sheetId))
  const toggle = (id: string) =>
    setSelected((current) =>
      current.includes(id) ? current.filter((item) => item !== id) : [...current, id],
    )
  return (
    <Dialog
      open={open}
      title="Quitar de varias hojas"
      onClose={onClose}
      footer={
        <>
          <Button appearance="secondary" onClick={onClose}>
            Cerrar
          </Button>
          <Button onClick={() => onSimulate(selected)} disabled={!selected.length || pending}>
            {pending ? 'Simulando…' : 'Ver qué pasaría'}
          </Button>
        </>
      }
    >
      <div className="revoke-dialog">
        <p>Seleccione las hojas para revisar el impacto antes de quitar acceso.</p>
        <ul>
          {detail.sheets.map((sheet) => {
            const reason =
              blocked(sheet.lockedReason) || (!sheet.editable ? 'No se puede administrar este acceso' : null)
            return (
              <li key={`${sheet.sheetId}-${sheet.shareId}-${sheet.scope}`}>
                <label>
                  {reason ? (
                    <input type="checkbox" disabled />
                  ) : (
                    <input
                      type="checkbox"
                      checked={selected.includes(sheet.sheetId)}
                      onChange={() => toggle(sheet.sheetId)}
                    />
                  )}
                  {sheet.sheetName}
                </label>
                {reason && <small>{reason}</small>}
              </li>
            )
          })}
        </ul>
        {error && <StatusAlert tone="error">{error.message}</StatusAlert>}
        {plan && (
          <section>
            <h3>Simulación</h3>
            <p>
              {Object.entries(plan.counts)
                .map(([action, count]) => `${action}: ${count}`)
                .join(' · ') || 'Sin cambios'}
            </p>
            <ul>
              {plan.steps.map((step) => (
                <li key={`${step.sheetId}-${step.action}`}>
                  <strong>{step.sheetName}</strong>
                  <span>
                    {step.action === 'REMOVE' ? 'Se quitaría' : 'Se omite'}
                    {step.reason && ` · ${step.reason}`}
                  </span>
                </li>
              ))}
            </ul>
            {readOnly && (
              <StatusAlert tone="info">Modo solo lectura: el panel no cambia nada en Smartsheet.</StatusAlert>
            )}
          </section>
        )}
      </div>
    </Dialog>
  )
}
