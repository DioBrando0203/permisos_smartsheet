import { healthHandlers } from './health'
import { mapHandlers } from './map'
import { sheetHandlers } from './sheets'

export const handlers = [...healthHandlers, ...sheetHandlers, ...mapHandlers]
