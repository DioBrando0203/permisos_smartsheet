export function parseRecipientEmails(value: string): {
  emails: string[]
  duplicates: string[]
  invalid: string[]
} {
  const values = value
    .split(/[\s,;]+/)
    .filter(Boolean)
    .map((email) => email.toLocaleLowerCase())
  const unique = new Set<string>()
  const duplicates = new Set<string>()
  const invalid: string[] = []
  for (const email of values) {
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) invalid.push(email)
    else if (unique.has(email)) duplicates.add(email)
    else unique.add(email)
  }
  return { emails: [...unique], duplicates: [...duplicates], invalid }
}
