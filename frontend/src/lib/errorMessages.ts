import type { ApiErrorCode } from './api'

export type ErrorMessage = { text: string; action: string | null }

const messages: Record<string, ErrorMessage> = {
  COORDINATES_OUT_OF_FLORIDA: { text: 'El punto está fuera de Florida.', action: null },
  SEGMENT_ROADWAY_MISMATCH: {
    text: 'A y B no están sobre la misma vía.',
    action: 'Elija dos puntos de la misma vía.',
  },
  SEGMENT_TOO_LONG: {
    text: 'El tramo supera la longitud máxima permitida.',
    action: 'Elija un tramo de menor longitud.',
  },
  GIS_UNAVAILABLE: {
    text: 'Los servicios del FDOT no responden; intenta en unos minutos.',
    action: 'Reintentar.',
  },
  GIS_DISABLED: { text: 'El mapa está deshabilitado en este servidor.', action: null },
  BACKEND_UNREACHABLE: {
    text: 'No se puede conectar con el backend del panel.',
    action: 'Inícielo con `python run.py` en `backend` y pulse Reintentar.',
  },
  TOKEN_MISSING: { text: 'Falta el token de Smartsheet en `backend/.env`.', action: null },
  SMARTSHEET_AUTH: {
    text: 'Smartsheet rechazó el token.',
    action: 'Genere uno nuevo y actualice `backend/.env`.',
  },
  SMARTSHEET_FORBIDDEN: {
    text: 'Smartsheet no permite esta operación con la cuenta del panel.',
    action: null,
  },
  SMARTSHEET_RATE_LIMITED: {
    text: 'Smartsheet está limitando las consultas.',
    action: 'Espere un minuto y pulse Reintentar.',
  },
  SMARTSHEET_UNAVAILABLE: { text: 'Smartsheet no respondió.', action: 'Reintentar.' },
  SMARTSHEET_REJECTED: { text: 'Smartsheet rechazó los datos.', action: null },
  READ_ONLY_MODE: { text: 'El panel está en modo solo lectura: no se cambió nada.', action: null },
  ORIGIN_NOT_ALLOWED: {
    text: 'Esta dirección no está autorizada para hacer cambios.',
    action: 'Abra el panel desde su dirección habitual.',
  },
  CANNOT_MANAGE_SHARES: {
    text: 'La cuenta del panel no es Administrador ni Propietario de esta hoja.',
    action: null,
  },
  NOT_SHARED_WITH_TOKEN: {
    text: 'La hoja es de otra persona y no está compartida con la cuenta del panel: sólo se consulta.',
    action: null,
  },
  OWNER_LOCKED: { text: 'El propietario no se cambia desde el panel.', action: 'Hágalo en Smartsheet.' },
  SHARE_INHERITED: { text: 'Este acceso viene del workspace.', action: 'Cámbielo en el workspace.' },
  OWNER_NOT_ASSIGNABLE: { text: 'No se puede dar el nivel Propietario.', action: null },
  DUPLICATE_RECIPIENTS: { text: 'Hay destinatarios repetidos.', action: 'Marque los chips repetidos.' },
  SHEET_NOT_FOUND: {
    text: 'La hoja no existe o la cuenta del panel no tiene acceso.',
    action: 'Vuelva a Hojas.',
  },
  SHARE_NOT_FOUND: {
    text: 'Ese acceso ya no existe; alguien lo cambió en Smartsheet.',
    action: 'Actualizar.',
  },
  PERSON_NOT_FOUND: { text: 'No se encontró a esa persona.', action: 'Vuelva a Personas.' },
  ROW_NOT_FOUND: { text: 'La fila o columna ya no existe.', action: null },
  COLUMN_NOT_FOUND: { text: 'La fila o columna ya no existe.', action: null },
  NO_CHECKS: { text: 'Seleccione al menos una comprobación.', action: null },
  TOO_MANY_COLUMNS: { text: 'Hay demasiadas columnas seleccionadas.', action: null },
  INVALID_PATTERN: { text: 'El patrón no es válido.', action: null },
  SAME_SHEET: { text: 'Elija dos hojas distintas.', action: null },
  VALIDATION: { text: 'Algún dato no es válido.', action: null },
}

export function errorMessage(code: ApiErrorCode, fallback?: string): ErrorMessage {
  return messages[code] ?? { text: fallback || 'Algo salió mal.', action: null }
}
