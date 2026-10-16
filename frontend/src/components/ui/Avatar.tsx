import { Person16Regular, Person20Regular } from '@fluentui/react-icons'

type Props = { name?: string | null; size?: 'sm' | 'md' }
const TONES = 10

function initials(name: string): string {
  const base = name.includes('@') && !name.trim().includes(' ') ? name.split('@')[0] : name
  const words = base
    .replace(/[^\p{L}\p{N}\s._-]/gu, ' ')
    .split(/[\s._-]+/)
    .filter(Boolean)
  return words.length > 1
    ? `${words[0][0]}${words.at(-1)?.[0] ?? ''}`.toUpperCase()
    : (words[0]?.[0] ?? '').toUpperCase()
}

function tone(name: string): number {
  return (
    ([...name.toLowerCase()].reduce((hash, char) => (hash * 31 + char.charCodeAt(0)) >>> 0, 0) % TONES) + 1
  )
}

export function Avatar({ name, size = 'md' }: Props) {
  const label = name?.trim() ? initials(name) : ''
  if (!label) {
    const Icon = size === 'sm' ? Person16Regular : Person20Regular
    return (
      <span className={`avatar avatar--${size} avatar--empty`} aria-hidden="true">
        <Icon />
      </span>
    )
  }
  return (
    <span className={`avatar avatar--${size}`} data-tone={tone(name ?? '')} aria-hidden="true">
      {label}
    </span>
  )
}
