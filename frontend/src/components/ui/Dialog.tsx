import type { ReactNode, RefObject } from 'react'
import { useEffect, useId, useRef } from 'react'

type Props = {
  open: boolean
  title: string
  children: ReactNode
  footer?: ReactNode
  initialFocusRef?: RefObject<HTMLElement | null>
  onClose: () => void
}

export function Dialog({ open, title, children, footer, initialFocusRef, onClose }: Props) {
  const dialog = useRef<HTMLDialogElement>(null)
  const previousFocus = useRef<HTMLElement | null>(null)
  const titleId = useId()
  useEffect(() => {
    const element = dialog.current
    if (!element) return
    if (open && !element.open) {
      previousFocus.current = document.activeElement instanceof HTMLElement ? document.activeElement : null
      element.showModal()
      window.requestAnimationFrame(() => initialFocusRef?.current?.focus())
    }
    if (!open && element.open) element.close()
  }, [initialFocusRef, open])
  const close = () => {
    previousFocus.current?.focus()
    onClose()
  }
  return (
    <dialog ref={dialog} className="dialog" aria-labelledby={titleId} onClose={close}>
      <section>
        <h2 id={titleId}>{title}</h2>
        <div className="dialog__body">{children}</div>
        {footer && <footer className="dialog__footer">{footer}</footer>}
      </section>
    </dialog>
  )
}
