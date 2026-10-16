import { Dismiss16Regular } from '@fluentui/react-icons'
import { useEffect } from 'react'

type Props = { children: string; onClose: () => void }

export function Toast({ children, onClose }: Props) {
  useEffect(() => {
    const timer = window.setTimeout(onClose, 5_000)
    return () => window.clearTimeout(timer)
  }, [onClose])
  return (
    <div className="toast" role="status">
      <span>{children}</span>
      <button type="button" aria-label="Cerrar aviso" onClick={onClose}>
        <Dismiss16Regular aria-hidden="true" />
      </button>
    </div>
  )
}
