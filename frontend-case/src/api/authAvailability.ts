/** 只读探测认证服务装配状态；不注册、不登录、不保存凭据。 */
import { apiRequest, ApiClientError } from './http'

export type AuthAvailability = 'loading' | 'available' | 'unavailable' | 'offline'

export async function checkAuthAvailability(): Promise<Exclude<AuthAvailability, 'loading'>> {
  try {
    // 无令牌时，已装配网关应明确返回 401；成功则仍视为可用。
    const response = await apiRequest<unknown>('/v1/auth/me')
    // Static SPA fallbacks can return HTTP 200 HTML for missing API routes.
    if (typeof response === 'object' && response !== null &&
        'user_id' in response && typeof response.user_id === 'string' &&
        'devices' in response && Array.isArray(response.devices)) return 'available'
    return 'unavailable'
  } catch (error) {
    if (error instanceof ApiClientError) {
      if (error.status === 401) return 'available'
      if (error.status === 503 && error.normalized.code === 'AUTH_UNAVAILABLE') {
        return 'unavailable'
      }
    }
    return 'offline'
  }
}
