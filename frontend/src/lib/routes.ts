export function sheetPath(id: string, tab?: string): string {
  const query = tab ? `?tab=${encodeURIComponent(tab)}` : ''
  return `/hojas/${encodeURIComponent(id)}${query}`
}

export function personPath(key: string): string {
  return `/personas/${encodeURIComponent(key)}`
}
