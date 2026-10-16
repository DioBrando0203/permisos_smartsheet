import { useRef } from 'react'
import { Button } from './Button'
import { Dialog } from './Dialog'

type Props = {
  open: boolean
  title: string
  children: string
  confirmLabel: string
  onConfirm: () => void
  onClose: () => void
}

export function ConfirmDialog({ open, title, children, confirmLabel, onConfirm, onClose }: Props) {
  const cancel = useRef<HTMLButtonElement>(null)
  return (
    <Dialog
      open={open}
      title={title}
      initialFocusRef={cancel}
      onClose={onClose}
      footer={
        <>
          <Button ref={cancel} appearance="secondary" onClick={onClose}>
            Cancelar
          </Button>
          <Button appearance="danger" onClick={onConfirm}>
            {confirmLabel}
          </Button>
        </>
      }
    >
      <p>{children}</p>
    </Dialog>
  )
}
