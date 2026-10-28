import { healthHandlers } from './health'
import { sheetHandlers } from './sheets'

export const handlers = [...healthHandlers, ...sheetHandlers]
