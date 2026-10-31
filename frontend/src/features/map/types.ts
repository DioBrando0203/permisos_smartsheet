export type RoadMatch = {
  roadwayId: string
  countyCodeFdot: string | null
  section: string | null
  subsection: string | null
  kind: 'state' | 'county' | 'other'
  route: string | null
  localName: string | null
  milepost: number | null
  distanceM: number
  beginPost: number | null
  endPost: number | null
}
export type MapPoint = {
  lat: number
  lon: number
  roads: RoadMatch[]
  location: {
    county: string | null
    countyCodeFdot: string | null
    fdotDistrict: string | null
    city: string | null
    zip: string | null
  }
  parcel: {
    parcelId: string
    countyCodeDor: string | null
    useCode: string | null
    useLabel: string | null
    publicOwner: string | null
    ownerName: string | null
    /** Fuente de la parcela: `fdacs_parcels` o el respaldo del condado (`broward_parcels`). */
    source: string
  } | null
  jurisdiction: {
    authority: string
    name: string | null
    basis: string
    confidence: 'high' | 'medium' | 'low'
    note: string
  }
  sources: { id: string; status: 'ok' | 'error' | 'timeout'; ms: number }[]
  warnings: string[]
}
/** Una fila de Work Location de OSP: una por cada vía que sigue el trazo (PEN-32). */
export type WorkLocation = {
  county: string | null
  /** Como en OSP: la ruta ("SR 953"); el ID de vía si no tiene ruta. */
  stateRoadId: string
  roadwayId: string
  sectionNumber: string | null
  beginningMilepost: number
  endingMilepost: number
  onTurnpike: boolean | null
  kind: RoadMatch['kind']
  localName: string | null
  lengthMi: number
  coordinates: [number, number][]
}
export type MapTrace = {
  /** Longitud de la polilínea marcada antes de ajustar a la LRS del FDOT. */
  inputLengthMi: number
  /** Longitud de las geometrías oficiales que se dibujan al terminar. */
  lengthMi: number
  rows: WorkLocation[]
  sources: MapPoint['sources']
  warnings: string[]
}
/** Contornos de parcelas de una celda, sólo con el ID (PEN-33). */
export type ParcelOutlines = {
  source: string
  parcels: { parcelId: string; rings: [number, number][][] }[]
  truncated: boolean
}
export type ApiRoadMatch = {
  roadway_id?: string
  county_code_fdot?: string | null
  section?: string | null
  subsection?: string | null
  kind?: RoadMatch['kind']
  route?: string | null
  local_name?: string | null
  milepost?: number | null
  distance_m?: number
  begin_post?: number | null
  end_post?: number | null
}
export type ApiMapPoint = {
  lat?: number
  lon?: number
  roads?: ApiRoadMatch[]
  location?: {
    county?: string | null
    county_code_fdot?: string | null
    fdot_district?: string | null
    city?: string | null
    zip?: string | null
  }
  parcel?: {
    parcel_id?: string
    county_code_dor?: string | null
    use_code?: string | null
    use_label?: string | null
    public_owner?: string | null
    owner_name?: string | null
    source?: string
  } | null
  jurisdiction?: {
    authority?: string
    name?: string | null
    basis?: string
    confidence?: 'high' | 'medium' | 'low'
    note?: string
  }
  sources?: { id?: string; status?: 'ok' | 'error' | 'timeout'; ms?: number }[]
  warnings?: string[]
}
export type ApiMapTrace = {
  path?: [number, number][]
  input_length_mi?: number
  length_mi?: number
  rows?: {
    county?: string | null
    state_road_id?: string
    roadway_id?: string
    section_number?: string | null
    beginning_milepost?: number
    ending_milepost?: number
    on_turnpike?: boolean | null
    kind?: RoadMatch['kind']
    local_name?: string | null
    length_mi?: number
    geometry?: { type?: 'LineString'; coordinates?: [number, number][] }
  }[]
  sources?: ApiMapPoint['sources']
  warnings?: string[]
}
export type ApiParcelOutlines = {
  source?: string
  parcels?: { parcel_id?: string; rings?: [number, number][][] }[]
  truncated?: boolean
}
export type MapSearchResult = {
  kind: 'coordinates' | 'address' | 'street' | 'milepost' | 'intersection' | 'nearest'
  label: string
  detail: string | null
  lat: number
  lon: number
  roadwayId: string | null
  milepost: number | null
  /** Sólo en `nearest`: las calles no se cruzan y este es su punto más cercano. */
  distanceM: number | null
}
export type MapSearch = { query: string; results: MapSearchResult[]; sources: MapPoint['sources'] }
export type ApiMapSearch = {
  query?: string
  results?: {
    kind?: MapSearchResult['kind']
    label?: string
    detail?: string | null
    lat?: number
    lon?: number
    roadway_id?: string | null
    milepost?: number | null
    distance_m?: number | null
  }[]
  sources?: ApiMapPoint['sources']
}
