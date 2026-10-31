import type { ApiMapArea, ApiMapCounty } from '../../features/map/area'
import type { ApiMapPoint, ApiMapSearch, ApiMapTrace, ApiParcelOutlines } from '../../features/map/types'

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

// Trazo del caso de control de OSP que además dobla a una calle local (fila "No estatal").
export const mapTraceFixture: ApiMapTrace = {
  path: [
    [25.771778, -80.26361],
    [25.782147, -80.264005],
  ],
  length_mi: 0.917,
  rows: [
    {
      county: 'Miami-Dade',
      state_road_id: 'SR 953',
      roadway_id: '87281000',
      section_number: '281',
      beginning_milepost: 3.124,
      ending_milepost: 3.839,
      on_turnpike: false,
      kind: 'state',
      local_name: 'LEJEUNE RD/NW 42 AVE',
      length_mi: 0.717,
      geometry: {
        type: 'LineString',
        coordinates: [
          [-80.26361, 25.771778],
          [-80.264005, 25.782147],
        ],
      },
    },
    {
      county: 'Miami-Dade',
      state_road_id: '87000442',
      roadway_id: '87000442',
      section_number: '000442',
      beginning_milepost: 0.1,
      ending_milepost: 0.304,
      on_turnpike: null,
      kind: 'other',
      local_name: 'NW 7 ST',
      length_mi: 0.2,
      geometry: { type: 'LineString', coordinates: [] },
    },
  ],
  sources: [
    { id: 'fdot_lrs', status: 'ok', ms: 300 },
    { id: 'fdot_turnpike', status: 'timeout', ms: 20000 },
  ],
  warnings: ['SOURCE_FAILED', 'NOT_STATE_ROAD'],
}

export const parcelOutlinesFixture: ApiParcelOutlines = {
  source: 'miami_dade_parcels',
  parcels: [
    {
      parcel_id: '300000000000',
      rings: [
        [
          [-80.2633, 25.772],
          [-80.26285, 25.772],
          [-80.26285, 25.7724],
          [-80.2633, 25.772],
        ],
      ],
    },
  ],
  truncated: false,
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

export const mapCountiesFixture: ApiMapCounty[] = [
  { name: 'Alachua', code_fdot: '26' },
  { name: 'Broward', code_fdot: '86' },
  { name: 'Miami-Dade', code_fdot: '87' },
]

const fortLauderdale = { west: -80.203854, south: 26.068973, east: -80.091544, north: 26.211925 }
export const mapAreaFixture: ApiMapArea = {
  county: 'Broward',
  code_fdot: '86',
  city: null,
  bounds: { west: -80.881236, south: 25.956775, east: -80.07474, north: 26.355552 },
  outline: [
    [
      [-80.88, 25.96],
      [-80.07, 25.96],
      [-80.07, 26.36],
      [-80.88, 25.96],
    ],
  ],
  cities: [
    { name: 'Fort Lauderdale', bounds: fortLauderdale },
    { name: 'Hollywood', bounds: { west: -80.25, south: 25.99, east: -80.11, north: 26.05 } },
  ],
}

// Cruce sobre vía del FDOT, con el milepost del cruce (como Las Olas y SE 3 Ave).
export const mapCrossingFixture: ApiMapSearch = {
  query: 'Las Olas & 3rd Ave',
  results: [
    {
      kind: 'intersection',
      label: 'E LAS OLAS BLVD y SE 3 AVE',
      detail: 'Broward · vía 86000142',
      lat: 26.119161,
      lon: -80.140422,
      roadway_id: '86000142',
      milepost: 0.258,
    },
  ],
  sources: [{ id: 'fdot_crossings', status: 'ok', ms: 900 }],
}
