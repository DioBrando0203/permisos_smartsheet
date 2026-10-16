type Props = { variant?: 'line' | 'title' | 'avatar' }

export function Skeleton({ variant = 'line' }: Props) {
  return <span className={`skeleton skeleton--${variant}`} aria-hidden="true" />
}
