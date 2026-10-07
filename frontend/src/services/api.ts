export const API_BASE_PATH = '/api/v1'

interface ErrorPayload {
  error: {
    code: string
    message: string
  }
}

export class ApiError extends Error {
  readonly code: string

  constructor(
    code: string,
    message: string,
  ) {
    super(message)
    this.name = 'ApiError'
    this.code = code
  }
}

export function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
}

function isErrorPayload(value: unknown): value is ErrorPayload {
  if (!isRecord(value) || !isRecord(value.error)) {
    return false
  }

  return (
    typeof value.error.code === 'string' &&
    typeof value.error.message === 'string'
  )
}

export async function apiRequest(
  path: string,
  options: RequestInit,
): Promise<unknown> {
  const headers = new Headers(options.headers)
  headers.set('Accept', 'application/json')
  if (options.body !== undefined) {
    headers.set('Content-Type', 'application/json')
  }

  const response = await fetch(`${API_BASE_PATH}${path}`, {
    ...options,
    credentials: 'include',
    headers,
  })
  const payload: unknown = await response.json()

  if (!response.ok) {
    if (isErrorPayload(payload)) {
      throw new ApiError(payload.error.code, payload.error.message)
    }
    throw new ApiError('TRANSFER_FAILED', 'Transfer could not be completed.')
  }

  return payload
}
