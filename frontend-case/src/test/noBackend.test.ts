import { afterEach, expect, it, vi } from 'vitest'
import { checkAuthAvailability } from '../api/authAvailability'
import { fetchMe, loginWithPairing, requestEmailCode, restoreBrowserSession, verifyEmailCode } from '../api/auth'

const originalFetch = globalThis.fetch
afterEach(() => { globalThis.fetch = originalFetch })

it('does not claim auth availability or sent mail for a static HTML fallback', async () => {
  globalThis.fetch = vi.fn(async () => ({
    ok: true, status: 200, json: async () => { throw new SyntaxError('HTML, not JSON') },
  })) as unknown as typeof fetch
  expect(await checkAuthAvailability()).toBe('unavailable')
  await expect(requestEmailCode('person@example.test')).rejects.toThrow('email service response invalid')
  await expect(verifyEmailCode('person@example.test', '000000')).rejects.toThrow('invalid authentication response')
  await expect(loginWithPairing('device', 'code')).rejects.toThrow('invalid authentication response')
  await expect(restoreBrowserSession()).rejects.toThrow('invalid authentication response')
  await expect(fetchMe('invalid')).rejects.toThrow('invalid identity response')
})

it('accepts only the documented email request acknowledgement', async () => {
  globalThis.fetch = vi.fn(async () => ({
    ok: true, status: 200, json: async () => ({ status: 'sent_if_available' }),
  })) as unknown as typeof fetch
  await expect(requestEmailCode('person@example.test')).resolves.toEqual({ status: 'sent_if_available' })
})
