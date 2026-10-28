export function formatNumber(value: number): string {
  return new Intl.NumberFormat('es-PE').format(value)
}

export function plural(count: number, singular: string, pluralText: string): string {
  return `${formatNumber(count)} ${count === 1 ? singular : pluralText}`
}

export function formatRelativeTime(value: string): string {
  const timestamp = Date.parse(value)
  if (Number.isNaN(timestamp)) return 'Fecha no disponible'
  const minutes = Math.max(0, Math.round((Date.now() - timestamp) / 60_000))
  if (minutes < 1) return 'hace un momento'
  if (minutes < 60) return `hace ${minutes} min`
  const hours = Math.round(minutes / 60)
  if (hours < 24) return `hace ${hours} h`
  const days = Math.round(hours / 24)
  return `hace ${days} día${days === 1 ? '' : 's'}`
}
