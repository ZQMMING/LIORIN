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

/** 匿名建号（会写数据库）；只能由用户明确点击触发。 */
export function registerAnonymous(): Promise<AuthTokens> {
  return apiRequest<AuthTokens>('/v1/auth/register', { method: 'POST' })
}

/** 现有后端只支持设备/配对码登录，不提供用户名密码登录。 */
export function requestEmailCode(email: string): Promise<{ status: 'sent_if_available' }> {
  return apiRequest('/v1/auth/email/request-code', { method: 'POST', body: { email } })
}

export function verifyEmailCode(email: string, code: string): Promise<AuthTokens> {
  return apiRequest('/v1/auth/email/verify', { method: 'POST', body: { email, code } })
}

export function loginWithPairing(deviceId: string, pairingCode: string): Promise<AuthTokens> {
  return apiRequest<AuthTokens>('/v1/auth/login', {
    method: 'POST', body: { device_id: deviceId, pairing_code: pairingCode },
  })
}

export function refreshSession(refreshToken: string): Promise<Omit<AuthTokens, 'user_id'>> {
  return apiRequest('/v1/auth/refresh', { method: 'POST', body: { refresh_token: refreshToken } })
}

export function fetchMe(accessToken: string): Promise<AuthMe> {
  return apiRequest<AuthMe>('/v1/auth/me', { token: accessToken })
}

export async function logout(accessToken: string, refreshToken: string): Promise<{ status: string }> {
  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), 10000)
  try {
    const result = await apiRequest<unknown>('/v1/auth/logout', {
      method: 'POST', token: accessToken, signal: controller.signal,
      body: { refresh_token: refreshToken, all_devices: false },
    })
    if (typeof result !== 'object' || result === null || !('status' in result) || result.status !== 'ok') {
      throw new Error('logout not confirmed')
    }
    return { status: 'ok' }
  } finally {
    clearTimeout(timer)
  }
}
