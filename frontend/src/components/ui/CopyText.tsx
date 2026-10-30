import { Copy16Regular } from '@fluentui/react-icons'
import { useState } from 'react'

export function CopyText({ value, label = 'Copiar código de soporte' }: { value: string; label?: string }) {
  const [copied, setCopied] = useState(false)
  const copy = async () => {
    await navigator.clipboard.writeText(value)
    setCopied(true)
  }
  return (
    <span className="copy-text">
      <code>{value}</code>
      <button type="button" aria-label={label} title={label} onClick={copy}>
        <Copy16Regular aria-hidden="true" />
      </button>
      {copied && <span>Copiado</span>}
    </span>
  )
}
