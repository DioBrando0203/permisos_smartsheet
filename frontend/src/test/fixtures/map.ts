import type { ApiMapPoint, ApiMapSearch, ApiMapSegment } from '../../features/map/types'

// Datos sintéticos con la forma de /api/map/*: el propietario nunca es real.
export const mapPointFixture: ApiMapPoint = {
  lat: 25.771778,
  lon: -80.26361,
  roads: [
    {
      roadway_id: '87281000',
      county_code_fdot: '87',
      section: '281',
      subsection: '000',
      kind: 'state',
      route: 'SR 953',
      local_name: 'LEJEUNE RD/NW 42 AVE',
      milepost: 3.124,
      distance_m: 0,
      begin_post: 0,
      end_post: 11.735,
    },
    { roadway_id: '87053000', kind: 'state', route: 'SR 968', milepost: 4.534, distance_m: 9.5 },
  ],
  location: { county: 'Miami-Dade', county_code_fdot: '87', fdot_district: '6', city: 'Miami', zip: '33126' },
  parcel: {
    parcel_id: '0000000000001',
    county_code_dor: '23',
    use_code: '094',
    use_label: 'Derecho de vía',
    public_owner: 'right_of_way',
    owner_name: 'PROPIETARIO SINTETICO 1',
    source: 'fdacs_parcels',
  },
  jurisdiction: {
    authority: 'FDOT',
    name: 'FDOT',
    basis: 'state_road',
    confidence: 'high',
    note: 'Vía estatal según FDOT.',
  },
  sources: [
    { id: 'fdot_lrs', status: 'ok', ms: 120 },
    { id: 'fdacs_parcels', status: 'timeout', ms: 20000 },
  ],
  warnings: ['MULTIPLE_ROADS', 'SOURCE_FAILED'],
}

export const mapSegmentFixture: ApiMapSegment = {
  start: mapPointFixture,
  end: { ...mapPointFixture, lat: 25.782147, lon: -80.264005 },
  road: mapPointFixture.roads?.[0],
  begin_milepost: 3.124,
  end_milepost: 3.839,
  length_mi: 0.717,
  geometry: {
    type: 'LineString',
    coordinates: [
      [-80.26361, 25.771778],
      [-80.264005, 25.782147],
    ],
  },
  osp_row: {
    county: 'Miami-Dade',
    state_road_id: '87281000',
    section_number: '281',
    beginning_milepost: 3.124,
    ending_milepost: 3.839,
  },
  jurisdiction: mapPointFixture.jurisdiction,
  warnings: [],
}

export const mapSearchFixture: ApiMapSearch = {
  query: 'SR 953 3.5',
  results: [
    {
      kind: 'milepost',
      label: 'SR 953 · MP 3.500',
      detail: 'Miami-Dade · vía 87281000',
      lat: 25.777229,
      lon: -80.26389,
      roadway_id: '87281000',
      milepost: 3.5,
    },
    {
      kind: 'street',
      label: 'LEJEUNE RD/NW 42 AVE',
      detail: 'Miami-Dade · vía 87281000',
      lat: 25.79,
      lon: -80.264,
    },
  ],
  sources: [{ id: 'census_geocoder', status: 'error', ms: 50 }],
}
