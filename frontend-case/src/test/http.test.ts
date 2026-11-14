/**
 * HTTP client 行为测试 —— FAIL FAST、不吞错、正确抛 ApiClientError。
 * 用全局 fetch mock 模拟后端响应。
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { apiRequest, ApiClientError } from '../api/http'
import { logout } from '../api/auth'

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
    vi.useRealTimers()
  })

  it('退出请求长时间无响应时中止，不会无限等待', async () => {
    vi.useFakeTimers()
    globalThis.fetch = vi.fn((_input, init) => new Promise((_resolve, reject) => {
      init?.signal?.addEventListener('abort', () => reject(new Error('aborted')))
    })) as typeof fetch
    const result = logout('access', 'refresh')
    const failure = expect(result).rejects.toThrow('aborted')
    await vi.advanceTimersByTimeAsync(10000)
    await failure
  })

  it('退出接口没有明确确认时不报告服务端退出成功', async () => {
    mockFetch(200, null)
    await expect(logout('access', 'refresh')).rejects.toThrow('logout not confirmed')
    mockFetch(200, { status: 'ok' })
    await expect(logout('access', 'refresh')).resolves.toEqual({ status: 'ok' })
  })

  it('2xx 返回原始 JSON', async () => {
    mockFetch(200, { ganZhi: [], weekday: '星期三' })
    const r = await apiRequest('/v1/today')
    expect(r).toEqual({ ganZhi: [], weekday: '星期三' })
  })

  it('内网代理使用相对 base，不产生双斜杠 URL', async () => {
    vi.stubEnv('VITE_API_BASE', '/')
    mockFetch(200, { status: 'ok' })
    await apiRequest('/v1/today')
    expect(globalThis.fetch).toHaveBeenCalledWith('/v1/today', expect.any(Object))
  })

  it('正式构建没有配置 API 地址时使用页面同源路径', async () => {
    vi.stubEnv('VITE_API_BASE', '')
    vi.stubEnv('PROD', true)
    mockFetch(200, { status: 'ok' })
    await apiRequest('/v1/today')
    expect(globalThis.fetch).toHaveBeenCalledWith('/v1/today', expect.any(Object))
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

  it('验证错误数组保留字段信息，异常错误结构不遮蔽 HTTP 状态', async () => {
    mockFetch(422, { detail: [{ loc: ['body', 'birth_date'], msg: 'invalid', type: 'date' }] })
    await expect(apiRequest('/v1/profile')).rejects.toMatchObject({ status: 422, normalized: { code: 'INVALID_INPUT', details: [{ loc: ['body', 'birth_date'] }] } })
    mockFetch(500, { error: null })
    await expect(apiRequest('/v1/profile')).rejects.toMatchObject({ status: 500, normalized: { code: 'UNKNOWN' } })
  })
})
