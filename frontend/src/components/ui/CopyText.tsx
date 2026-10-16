import { Copy16Regular } from '@fluentui/react-icons'
import { useState } from 'react'

export function CopyText({ value }: { value: string }) {
  const [copied, setCopied] = useState(false)
  const copy = async () => {
    await navigator.clipboard.writeText(value)
    setCopied(true)
  }
  return (
    <span className="copy-text">
      <code>{value}</code>
      <button type="button" aria-label="Copiar código de soporte" onClick={copy}>
        <Copy16Regular aria-hidden="true" />
      </button>
      {copied && <span>Copiado</span>}
    </span>
  )
}
