/** Nombre legible de cada fuente GIS de un punto (SPEC-B14). */
export const sourceNames: Record<string, string> = {
  fdot_lrs: 'Vías y milepost (FDOT)',
  fdot_state_roads: 'Vías estatales (FDOT)',
  fdot_county_roads: 'Vías de condado (FDOT)',
  fdot_local_names: 'Nombres de calles (FDOT)',
  fdot_counties: 'Condados (FDOT)',
  fdot_cities: 'Ciudades (FDOT)',
  fdot_zip: 'Códigos ZIP (FDOT)',
  fdacs_parcels: 'Parcelas (FDACS)',
  broward_parcels: 'Parcelas de Broward (condado)',
  fdot_turnpike: 'Distritos y Turnpike (FDOT)',
}

/** De dónde salió la parcela: FDACS trae uso y propietario; el respaldo del condado, sólo el ID. */
export const parcelSources: Record<string, string> = {
  fdacs_parcels: 'FDACS (datos del tasador)',
  broward_parcels: 'Condado de Broward (sólo el folio)',
}
