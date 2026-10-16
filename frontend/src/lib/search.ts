export function searchText(value: string): string {
  return value
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLocaleLowerCase()
}

export function includesSearch(value: string, query: string): boolean {
  return searchText(value).includes(searchText(query).trim())
}
