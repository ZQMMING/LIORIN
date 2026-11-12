/**
 * HTTP client 行为测试 —— FAIL FAST、不吞错、正确抛 ApiClientError。
 * 用全局 fetch mock 模拟后端响应。
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { apiRequest, ApiClientError } from '../api/http'

const originalFetch = globalThis.fetch

function mockFetch(status: number, body: unknown) {
  globalThis.fetch = vi.fn(async () => ({
    ok: status >= 200 && status < 300,
    status,
    json: async () => body,
  })) as unknown as typeof fetch
}

describe('apiRequest', () => {
  beforeEach(() => {
    vi.stubEnv('VITE_API_BASE', 'http://127.0.0.1:8000')
  })
  afterEach(() => {
    globalThis.fetch = originalFetch
    vi.unstubAllEnvs()
  })

  it('2xx 返回原始 JSON', async () => {
    mockFetch(200, { ganZhi: [], weekday: '星期三' })
    const r = await apiRequest('/v1/today')
    expect(r).toEqual({ ganZhi: [], weekday: '星期三' })
  })

  it('POST 带 JSON body 和 Content-Type', async () => {
    mockFetch(200, { profile_status: 'VALID' })
    await apiRequest('/v1/profile', { method: 'POST', body: { gender: 'male' } })
    const call = (globalThis.fetch as ReturnType<typeof vi.fn>).mock.calls[0]
    expect(call[1].method).toBe('POST')
    expect(call[1].headers['Content-Type']).toBe('application/json')
    expect(JSON.parse(call[1].body)).toEqual({ gender: 'male' })
  })

  it('非 2xx 抛 ApiClientError（形态 A 归一化）', async () => {
    mockFetch(422, {
      error: { code: 'INSUFFICIENT_INPUT', message: 'missing timezone+location' },
    })
    await expect(apiRequest('/v1/profile', { method: 'POST', body: {} }))
      .rejects.toBeInstanceOf(ApiClientError)
    await expect(apiRequest('/v1/profile', { method: 'POST', body: {} }))
      .rejects.toMatchObject({ status: 422, normalized: { code: 'INSUFFICIENT_INPUT' } })
  })

  it('非 2xx 抛 ApiClientError（形态 B 归一化）', async () => {
    mockFetch(503, { detail: { code: 'AUTH_UNAVAILABLE', message: 'gateway not initialised' } })
    await expect(apiRequest('/v1/auth/me'))
      .rejects.toMatchObject({ status: 503, normalized: { code: 'AUTH_UNAVAILABLE' } })
  })

  it('非 JSON 响应体不抛额外异常（body 为 null 时仍抛 status 错误）', async () => {
    globalThis.fetch = vi.fn(async () => ({
      ok: false,
      status: 500,
      json: async () => { throw new Error('not json') },
    })) as unknown as typeof fetch
    await expect(apiRequest('/health'))
      .rejects.toMatchObject({ status: 500, normalized: { code: 'UNKNOWN' } })
  })
})
