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
export type MapSegment = {
  start: MapPoint
  end: MapPoint
  road: RoadMatch
  beginMilepost: number
  endMilepost: number
  lengthMi: number
  geometry: { type: 'LineString'; coordinates: [number, number][] }
  ospRow: {
    county: string | null
    stateRoadId: string
    sectionNumber: string | null
    beginningMilepost: number
    endingMilepost: number
  }
  jurisdiction: MapPoint['jurisdiction']
  warnings: string[]
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
export type ApiMapSegment = {
  start?: ApiMapPoint
  end?: ApiMapPoint
  road?: ApiRoadMatch
  begin_milepost?: number
  end_milepost?: number
  length_mi?: number
  geometry?: { type?: 'LineString'; coordinates?: [number, number][] }
  osp_row?: {
    county?: string | null
    state_road_id?: string
    section_number?: string | null
    beginning_milepost?: number
    ending_milepost?: number
  }
  jurisdiction?: ApiMapPoint['jurisdiction']
  warnings?: string[]
}
export type MapSearchResult = {
  kind: 'coordinates' | 'address' | 'street' | 'milepost'
  label: string
  detail: string | null
  lat: number
  lon: number
  roadwayId: string | null
  milepost: number | null
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
  }[]
  sources?: ApiMapPoint['sources']
}
