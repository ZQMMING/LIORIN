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
export function loginWithPairing(deviceId: string, pairingCode: string): Promise<AuthTokens> {
  return apiRequest<AuthTokens>('/v1/auth/login', {
    method: 'POST', body: { device_id: deviceId, pairing_code: pairingCode },
  })
}

export function fetchMe(accessToken: string): Promise<AuthMe> {
  return apiRequest<AuthMe>('/v1/auth/me', { token: accessToken })
}

export function logout(accessToken: string, refreshToken: string): Promise<{ status: string }> {
  return apiRequest('/v1/auth/logout', {
    method: 'POST', token: accessToken,
    body: { refresh_token: refreshToken, all_devices: false },
  })
}
