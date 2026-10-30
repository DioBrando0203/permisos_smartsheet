import type { ApiMapPoint, ApiMapSegment, ApiRoadMatch, MapPoint, MapSegment, RoadMatch } from './types'

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
export function normalizeMapSegment(source: ApiMapSegment): MapSegment {
  const start = normalizeMapPoint(source.start ?? {})
  return {
    start,
    end: normalizeMapPoint(source.end ?? {}),
    road: road(source.road ?? {}),
    beginMilepost: source.begin_milepost ?? 0,
    endMilepost: source.end_milepost ?? 0,
    lengthMi: source.length_mi ?? 0,
    geometry: { type: 'LineString', coordinates: source.geometry?.coordinates ?? [] },
    ospRow: {
      county: source.osp_row?.county ?? null,
      stateRoadId: source.osp_row?.state_road_id ?? '',
      sectionNumber: source.osp_row?.section_number ?? null,
      beginningMilepost: source.osp_row?.beginning_milepost ?? 0,
      endingMilepost: source.osp_row?.ending_milepost ?? 0,
    },
    jurisdiction: source.jurisdiction
      ? normalizeMapPoint({ jurisdiction: source.jurisdiction }).jurisdiction
      : start.jurisdiction,
    warnings: source.warnings ?? [],
  }
}
