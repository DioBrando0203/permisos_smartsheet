import type { MapSegment } from '../types'

export function ospText(segment: MapSegment): string {
  const row = segment.ospRow
  return [
    row.county ?? '',
    row.stateRoadId,
    row.sectionNumber ?? '',
    row.beginningMilepost,
    row.endingMilepost,
  ].join('\t')
}
