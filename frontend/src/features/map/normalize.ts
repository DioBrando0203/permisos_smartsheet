import type {
  ApiMapPoint,
  ApiMapSearch,
  ApiMapTrace,
  ApiParcelOutlines,
  ApiRoadMatch,
  MapPoint,
  MapSearch,
  MapTrace,
  ParcelOutlines,
  RoadMatch,
} from './types'

function road(source: ApiRoadMatch): RoadMatch {
  return {
    roadwayId: source.roadway_id ?? '',
    countyCodeFdot: source.county_code_fdot ?? null,
    section: source.section ?? null,
    subsection: source.subsection ?? null,
    kind: source.kind ?? 'other',
    route: source.route ?? null,
    localName: source.local_name ?? null,
    milepost: source.milepost ?? null,
    distanceM: source.distance_m ?? 0,
    beginPost: source.begin_post ?? null,
    endPost: source.end_post ?? null,
  }
}
export function normalizeMapPoint(source: ApiMapPoint): MapPoint {
  return {
    lat: source.lat ?? 0,
    lon: source.lon ?? 0,
    roads: (source.roads ?? []).map(road),
    location: {
      county: source.location?.county ?? null,
      countyCodeFdot: source.location?.county_code_fdot ?? null,
      fdotDistrict: source.location?.fdot_district ?? null,
      city: source.location?.city ?? null,
      zip: source.location?.zip ?? null,
    },
    parcel: source.parcel
      ? {
          parcelId: source.parcel.parcel_id ?? '',
          countyCodeDor: source.parcel.county_code_dor ?? null,
          useCode: source.parcel.use_code ?? null,
          useLabel: source.parcel.use_label ?? null,
          publicOwner: source.parcel.public_owner ?? null,
          ownerName: source.parcel.owner_name ?? null,
          source: source.parcel.source ?? 'fdacs_parcels',
        }
      : null,
    jurisdiction: {
      authority: source.jurisdiction?.authority ?? 'UNKNOWN',
      name: source.jurisdiction?.name ?? null,
      basis: source.jurisdiction?.basis ?? 'no_road',
      confidence: source.jurisdiction?.confidence ?? 'low',
      note: source.jurisdiction?.note ?? '',
    },
    sources: (source.sources ?? []).map((item) => ({
      id: item.id ?? '',
      status: item.status ?? 'error',
      ms: item.ms ?? 0,
    })),
    warnings: source.warnings ?? [],
  }
}
export function normalizeMapTrace(source: ApiMapTrace): MapTrace {
  return {
    inputLengthMi: source.input_length_mi ?? source.length_mi ?? 0,
    lengthMi: source.length_mi ?? null,
    matchedPercent: source.matched_percent ?? null,
    unmatchedLengthMi: source.unmatched_length_mi ?? null,
    adjustment: source.adjustment
      ? { startM: source.adjustment.start_m ?? null, endM: source.adjustment.end_m ?? null }
      : null,
    rows: (source.rows ?? []).map((row) => ({
      county: row.county ?? null,
      stateRoadId: row.state_road_id ?? row.roadway_id ?? '',
      roadwayId: row.roadway_id ?? '',
      sectionNumber: row.section_number ?? null,
      beginningMilepost: row.beginning_milepost ?? 0,
      endingMilepost: row.ending_milepost ?? 0,
      onTurnpike: row.on_turnpike ?? null,
      kind: row.kind ?? 'other',
      localName: row.local_name ?? null,
      lengthMi: row.length_mi ?? null,
      coordinates: row.geometry?.coordinates ?? [],
    })),
    sources: normalizeMapPoint({ sources: source.sources }).sources,
    warnings: source.warnings ?? [],
  }
}
export function normalizeParcelOutlines(source: ApiParcelOutlines): ParcelOutlines {
  return {
    source: source.source ?? '',
    parcels: (source.parcels ?? []).map((parcel) => ({
      parcelId: parcel.parcel_id ?? '',
      rings: parcel.rings ?? [],
    })),
    truncated: source.truncated ?? false,
  }
}
export function normalizeMapSearch(source: ApiMapSearch): MapSearch {
  return {
    query: source.query ?? '',
    results: (source.results ?? []).map((item) => ({
      kind: item.kind ?? 'coordinates',
      label: item.label ?? '',
      detail: item.detail ?? null,
      lat: item.lat ?? 0,
      lon: item.lon ?? 0,
      roadwayId: item.roadway_id ?? null,
      milepost: item.milepost ?? null,
      distanceM: item.distance_m ?? null,
    })),
    sources: normalizeMapPoint({ sources: source.sources }).sources,
  }
}
