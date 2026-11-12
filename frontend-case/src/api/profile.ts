/**
 * Profile API client — POST /v1/profile
 *
 * 请求体 ProfileRequest（嵌套 birth_time），与 ReadingRequest（扁平 hour）不同。
 */

import { apiRequest } from './http'
import type { ProfileRequest, ProfileResponse } from '../contracts/profile'

export async function submitProfile(req: ProfileRequest): Promise<ProfileResponse> {
  return apiRequest<ProfileResponse>('/v1/profile', { method: 'POST', body: req })
}
