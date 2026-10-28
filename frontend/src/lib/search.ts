export function searchText(value: string): string {
  return value
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLocaleLowerCase()
}

export function includesSearch(value: string, query: string): boolean {
  const terms = searchText(query)
    .split(/\s+/)
    .filter((term) => term.length > 1 && !['de', 'del', 'el', 'la', 'las', 'los', 'y'].includes(term))
  const source = searchText(value)
  return terms.every((term) => source.includes(term))
}
