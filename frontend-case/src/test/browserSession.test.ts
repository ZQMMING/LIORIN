import { afterEach, describe, expect, it, vi } from 'vitest'
import { logout, restoreBrowserSession, verifyEmailCode } from '../api/auth'

const originalFetch = globalThis.fetch
afterEach(() => { globalThis.fetch = originalFetch; vi.unstubAllEnvs() })

describe('browser session protocol', () => {
  it('requests cookie mode without storing credentials in web storage', async () => {
    vi.stubEnv('VITE_API_BASE', '/')
    globalThis.fetch = vi.fn(async () => ({ ok: true, status: 200, json: async () => ({ refresh_token: '' }) })) as unknown as typeof fetch
    await verifyEmailCode('user@example.test', '123456')
    expect(globalThis.fetch).toHaveBeenCalledWith('/v1/auth/email/verify', expect.objectContaining({
      headers: expect.objectContaining({ 'X-Liorin-Session': 'cookie' }),
    }))
    expect(window.localStorage.length).toBe(0)
    expect(window.sessionStorage.length).toBe(0)
  })

  it('deduplicates concurrent restore calls and uses cookie logout', async () => {
    vi.stubEnv('VITE_API_BASE', '/')
    globalThis.fetch = vi.fn(async () => ({ ok: true, status: 200, json: async () => ({ status: 'ok' }) })) as unknown as typeof fetch
    await Promise.all([restoreBrowserSession(), restoreBrowserSession()])
    expect(globalThis.fetch).toHaveBeenCalledTimes(1)
    await logout('access', '')
    expect(globalThis.fetch).toHaveBeenLastCalledWith('/v1/auth/session/logout', expect.objectContaining({
      method: 'POST', headers: expect.objectContaining({ Authorization: 'Bearer access' }),
    }))
  })
})
