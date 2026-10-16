export function formatNumber(value: number): string {
  return new Intl.NumberFormat('es-PE').format(value)
}

export function plural(count: number, singular: string, pluralText: string): string {
  return `${formatNumber(count)} ${count === 1 ? singular : pluralText}`
}
