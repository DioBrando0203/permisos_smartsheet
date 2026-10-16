import type { AccessLevel } from './types'

export type AccessLevelInfo = { label: string; description: string; rank: number }

export const accessLevels: Record<AccessLevel, AccessLevelInfo> = {
  VIEWER: { label: 'Visor', description: 'Ver', rank: 1 },
  COMMENTER: { label: 'Comentarista', description: 'Ver y comentar', rank: 2 },
  EDITOR: { label: 'Editor', description: 'Editar filas', rank: 3 },
  EDITOR_SHARE: { label: 'Editor que comparte', description: 'Editar y compartir', rank: 4 },
  ADMIN: { label: 'Administrador', description: 'Todo menos eliminar la hoja', rank: 5 },
  OWNER: { label: 'Propietario', description: 'Propietario de la hoja', rank: 6 },
}
