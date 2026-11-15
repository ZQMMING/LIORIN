import { apiRequest } from './http'

export interface AuthTokens {
  user_id: string
  access_token: string
  refresh_token: string
  expires_in: number
  token_version: number
}

export interface AuthMe {
  user_id: string
  is_new_user: boolean
  has_birth_info: boolean
  has_heluo_model: boolean
  devices: Array<{ id: string; device_type: string; status: string }>
}

function requireTokens(value: unknown): AuthTokens {
  if (typeof value !== 'object' || value === null) throw new Error('invalid authentication response')
  const data = value as Partial<AuthTokens>
  if (typeof data.user_id !== 'string' || !data.user_id ||
      typeof data.access_token !== 'string' || !data.access_token ||
      typeof data.refresh_token !== 'string' || typeof data.expires_in !== 'number' ||
      !Number.isFinite(data.expires_in) || data.expires_in <= 0 ||
      !Number.isInteger(data.token_version)) throw new Error('invalid authentication response')
  return data as AuthTokens
}

/** 匿名建号（会写数据库）；只能由用户明确点击触发。 */
export function registerAnonymous(): Promise<AuthTokens> {
  return apiRequest<AuthTokens>('/v1/auth/register', { method: 'POST' })
}

/** 现有后端只支持设备/配对码登录，不提供用户名密码登录。 */
export async function requestEmailCode(email: string): Promise<{ status: 'sent_if_available' }> {
  const result = await apiRequest<unknown>('/v1/auth/email/request-code', { method: 'POST', body: { email } })
  if (typeof result !== 'object' || result === null || !('status' in result) || result.status !== 'sent_if_available') {
    throw new Error('email service response invalid')
  }
  return { status: 'sent_if_available' }
}

export async function verifyEmailCode(email: string, code: string): Promise<AuthTokens> {
  return requireTokens(await apiRequest('/v1/auth/email/verify', { method: 'POST', body: { email, code }, headers: { 'X-Liorin-Session': 'cookie' } }))
}

let restorePending: Promise<AuthTokens> | null = null

export function restoreBrowserSession(): Promise<AuthTokens> {
  // React StrictMode may mount twice; a single rotating cookie must not be
  // presented concurrently within the same page.
  if (!restorePending) {
    restorePending = apiRequest<unknown>('/v1/auth/session/restore', { method: 'POST' }).then(requireTokens)
      .finally(() => { restorePending = null })
  }
  return restorePending
}

export async function loginWithPairing(deviceId: string, pairingCode: string): Promise<AuthTokens> {
  return requireTokens(await apiRequest('/v1/auth/login', {
    method: 'POST', body: { device_id: deviceId, pairing_code: pairingCode },
  }))
}

export function refreshSession(refreshToken: string): Promise<Omit<AuthTokens, 'user_id'>> {
  return apiRequest('/v1/auth/refresh', { method: 'POST', body: { refresh_token: refreshToken } })
}

export async function fetchMe(accessToken: string): Promise<AuthMe> {
  const result = await apiRequest<unknown>('/v1/auth/me', { token: accessToken })
  if (typeof result !== 'object' || result === null || !('user_id' in result) ||
      typeof result.user_id !== 'string' || !result.user_id ||
      !('devices' in result) || !Array.isArray(result.devices)) throw new Error('invalid identity response')
  return result as AuthMe
}

export async function logout(accessToken: string, refreshToken: string): Promise<{ status: string }> {
  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), 10000)
  try {
    const cookieSession = !refreshToken
    const result = await apiRequest<unknown>(cookieSession ? '/v1/auth/session/logout' : '/v1/auth/logout', {
      method: 'POST', token: accessToken, signal: controller.signal,
      body: cookieSession ? undefined : { refresh_token: refreshToken, all_devices: false },
    })
    if (typeof result !== 'object' || result === null || !('status' in result) || result.status !== 'ok') {
      throw new Error('logout not confirmed')
    }
    return { status: 'ok' }
  } finally {
    clearTimeout(timer)
  }
}
