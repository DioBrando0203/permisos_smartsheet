const REQUEST_TIMEOUT_MS = 120_000

export type ApiErrorCode = string

export class ApiError extends Error {
  readonly code: ApiErrorCode
  readonly refId: string | null
  readonly status: number | null
  readonly upstreamMessage: string | null

  constructor({
    code,
    message,
    refId = null,
    status = null,
    upstreamMessage = null,
  }: {
    code: ApiErrorCode
    message: string
    refId?: string | null
    status?: number | null
    upstreamMessage?: string | null
  }) {
    super(message)
    this.name = 'ApiError'
    this.code = code
    this.refId = refId
    this.status = status
    this.upstreamMessage = upstreamMessage
  }
}

type ErrorBody = { detail?: unknown }
type ErrorDetail = {
  code?: string
  message?: string
  ref_id?: string | null
  upstream_message?: string | null
}

function isErrorBody(value: unknown): value is ErrorBody {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
}

function isErrorDetail(value: unknown): value is ErrorDetail {
  return isErrorBody(value)
}

async function responseError(response: Response): Promise<ApiError> {
  let body: unknown
  try {
    body = await response.json()
  } catch {
    return new ApiError({ code: 'UNKNOWN', message: 'Algo salió mal.', status: response.status })
  }
  if (isErrorBody(body) && Array.isArray(body.detail)) {
    return new ApiError({ code: 'VALIDATION', message: 'Algún dato no es válido.', status: response.status })
  }
  if (isErrorBody(body) && isErrorDetail(body.detail)) {
    const detail = body.detail
    return new ApiError({
      code: detail.code ?? 'UNKNOWN',
      message: detail.message ?? 'Algo salió mal.',
      refId: detail.ref_id ?? null,
      status: response.status,
      upstreamMessage: detail.upstream_message ?? null,
    })
  }
  return new ApiError({ code: 'UNKNOWN', message: 'Algo salió mal.', status: response.status })
}

export async function api<T>(path: string, init: RequestInit = {}): Promise<T> {
  const controller = new AbortController()
  const timer = window.setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS)
  try {
    const response = await fetch(path, {
      ...init,
      headers: { Accept: 'application/json', ...init.headers },
      signal: controller.signal,
    })
    if (!response.ok) throw await responseError(response)
    return (await response.json()) as T
  } catch (error) {
    if (error instanceof ApiError) throw error
    throw new ApiError({
      code: 'BACKEND_UNREACHABLE',
      message: 'No se puede conectar con el backend del panel.',
    })
  } finally {
    window.clearTimeout(timer)
  }
}
