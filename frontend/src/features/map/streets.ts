/** Calles del condado con quién las mantiene: capa por celdas y calles del trazo (PEN-41). */
type Path = [number, number][]

export type StreetLine = {
  id: string
  name: string | null
  /** Valor del condado tal cual ("St Johns County", "Private CDD"…). */
  maintainer: string
  /** `null` si el condado no dice quién la mantiene (Proposed, Emergency Access…). */
  authority: string | null
  authorityName: string | null
  gated: boolean
  paths: Path[]
}
export type StreetLines = {
  /** `null` fuera de todo condado con fuente propia (hoy sólo St. Johns). */
  source: string | null
  county: string | null
  streets: StreetLine[]
  truncated: boolean
}
export type TraceStreet = Omit<StreetLine, 'id'> & { lengthMi: number }
export type TraceStreets = {
  county: string | null
  source: string | null
  streets: TraceStreet[]
  unmatchedLengthMi: number
  sources: { id: string; status: 'ok' | 'error' | 'timeout'; ms: number }[]
  warnings: string[]
}

type ApiStreet = {
  id?: string
  name?: string | null
  maintainer?: string
  authority?: string | null
  authority_name?: string | null
  gated?: boolean
  paths?: number[][][]
  length_mi?: number
}
export type ApiStreetLines = {
  source?: string | null
  county?: string | null
  streets?: ApiStreet[]
  truncated?: boolean
}
export type ApiTraceStreets = {
  county?: string | null
  source?: string | null
  streets?: ApiStreet[]
  unmatched_length_mi?: number
  sources?: { id?: string; status?: 'ok' | 'error' | 'timeout'; ms?: number }[]
  warnings?: string[]
}

const paths = (source?: number[][][]): Path[] =>
  (source ?? []).map((path) => path.map(([lon, lat]) => [lon ?? 0, lat ?? 0] as [number, number]))

function street(source: ApiStreet): Omit<StreetLine, 'id'> {
  return {
    name: source.name ?? null,
    maintainer: source.maintainer ?? '',
    authority: source.authority ?? null,
    authorityName: source.authority_name ?? null,
    gated: Boolean(source.gated),
    paths: paths(source.paths),
  }
}

export function normalizeStreetLines(source: ApiStreetLines): StreetLines {
  return {
    source: source.source ?? null,
    county: source.county ?? null,
    streets: (source.streets ?? []).map((item) => ({ id: item.id ?? '', ...street(item) })),
    truncated: Boolean(source.truncated),
  }
}

export function normalizeTraceStreets(source: ApiTraceStreets): TraceStreets {
  return {
    county: source.county ?? null,
    source: source.source ?? null,
    streets: (source.streets ?? []).map((item) => ({ ...street(item), lengthMi: item.length_mi ?? 0 })),
    unmatchedLengthMi: source.unmatched_length_mi ?? 0,
    sources: (source.sources ?? []).map((item) => ({
      id: item.id ?? '',
      status: item.status ?? 'error',
      ms: item.ms ?? 0,
    })),
    warnings: source.warnings ?? [],
  }
}
