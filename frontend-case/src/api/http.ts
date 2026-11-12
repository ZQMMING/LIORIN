/**
 * HTTP client — 极薄封装
 *
 * base URL 走环境变量 VITE_API_BASE，默认 http://127.0.0.1:8000。
 * 不做任何字段兼容猜测：请求失败/响应不符合契约即抛 ApiClientError（FAIL FAST）。
 */

import { normalizeApiError, type NormalizedApiError } from '../contracts/errors'

const DEFAULT_BASE = 'http://127.0.0.1:8000'

export class ApiClientError extends Error {
  readonly normalized: NormalizedApiError
  readonly status: number

  constructor(message: string, status: number, normalized: NormalizedApiError) {
    super(message)
    this.name = 'ApiClientError'
    this.status = status
    this.normalized = normalized
  }
}

function baseUrl(): string {
  return (import.meta.env.VITE_API_BASE as string | undefined) ?? DEFAULT_BASE
}

interface RequestOptions {
  method?: 'GET' | 'POST'
  body?: unknown
  token?: string | null
}

/**
 * 底层请求。不吞错：非 2xx 抛 ApiClientError，2xx 返回原始 JSON。
 */
export async function apiRequest<T = unknown>(
  path: string,
  opts: RequestOptions = {},
): Promise<T> {
  const headers: Record<string, string> = { Accept: 'application/json' }
  if (opts.body !== undefined) headers['Content-Type'] = 'application/json'
  if (opts.token) headers['Authorization'] = `Bearer ${opts.token}`

  const res = await fetch(`${baseUrl()}${path}`, {
    method: opts.method ?? 'GET',
    headers,
    body: opts.body !== undefined ? JSON.stringify(opts.body) : undefined,
  })

  let body: unknown = null
  try {
    body = await res.json()
  } catch {
    body = null
  }

  if (!res.ok) {
    const normalized = normalizeApiError(body)
    throw new ApiClientError(
      `${res.status} ${normalized.code}: ${normalized.message}`,
      res.status,
      normalized,
    )
  }

  return body as T
}
