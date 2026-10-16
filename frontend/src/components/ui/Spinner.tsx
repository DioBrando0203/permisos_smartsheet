type Props = { size?: 'sm' | 'md' | 'lg'; label?: string }

export function Spinner({ size = 'md', label }: Props) {
  return (
    <span
      className={`spinner spinner--${size}`}
      role={label ? 'status' : undefined}
      aria-hidden={label ? undefined : true}
    >
      {label && <span className="sr-only">{label}</span>}
    </span>
  )
}
