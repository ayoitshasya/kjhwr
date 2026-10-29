import type {
  AccuracyResponse,
  ActualsResponse,
  ComparisonResponse,
  ErrorResponse,
  ForecastResponse,
  HealthResponse,
} from './types'

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

export class ApiError extends Error {
  status: number
  code: string

  constructor(status: number, code: string, message: string) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.code = code
  }
}

async function get<T>(path: string, params: Record<string, string | number | undefined>): Promise<T> {
  const query = new URLSearchParams()
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined) query.set(key, String(value))
  }
  const url = `${BASE_URL}${path}?${query.toString()}`

  const response = await fetch(url)
  if (!response.ok) {
    let detail: ErrorResponse | null = null
    try {
      detail = await response.json()
    } catch {
      // body wasn't JSON - fall through to generic message below
    }
    throw new ApiError(
      response.status,
      detail?.error.code ?? 'unknown_error',
      detail?.error.message ?? `Request to ${path} failed with status ${response.status}`,
    )
  }
  return response.json() as Promise<T>
}

export const api = {
  health: () => get<HealthResponse>('/api/health', {}),

  forecast: (date: string, confidence?: number) =>
    get<ForecastResponse>('/api/forecast', { date, confidence }),

  actuals: (from: string, to: string) => get<ActualsResponse>('/api/actuals', { from, to }),

  comparison: (from: string, to: string) =>
    get<ComparisonResponse>('/api/comparison', { from, to }),

  accuracy: (from: string, to: string, confidence?: number) =>
    get<AccuracyResponse>('/api/accuracy', { from, to, confidence }),
}
