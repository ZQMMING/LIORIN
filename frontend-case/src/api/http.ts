/**
 * HTTP client — 极薄封装
 *
 * VITE_API_BASE 可覆盖地址；正式构建默认同源，开发模式默认本机后端。
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
  // 内网测试统一走 Vite 同源代理，避免手机端访问自己的 127.0.0.1。
  if (import.meta.env.VITE_LIORIN_LAN_TEST === '1' ||
      import.meta.env.VITE_LIORIN_LOCAL_PREVIEW === '1') return '/'
  const configured = (import.meta.env.VITE_API_BASE as string | undefined)?.trim()
  return configured || (import.meta.env.PROD ? '/' : DEFAULT_BASE)
}

interface RequestOptions {
  method?: 'GET' | 'POST' | 'PUT'
  body?: unknown
  token?: string | null
  signal?: AbortSignal
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

  const base = baseUrl().replace(/\/$/, '')
  const res = await fetch(`${base}${path}`, {
    method: opts.method ?? 'GET',
    headers,
    signal: opts.signal,
    body: opts.body !== undefined ? JSON.stringify(opts.body) : undefined,
  })

  let body: unknown = null
  try {
    body = await res.json()
  } catch (error) {
    if (opts.signal?.aborted) throw error
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
