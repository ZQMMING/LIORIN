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

/** 独立持久化端点；与旧的无状态 /v1/profile 回执严格区分。 */
export function saveStoredProfile(req: ProfileRequest, token: string): Promise<{ profile_status: 'VALID'; stored: true; trace_id: string }> {
  return apiRequest('/v1/profile/stored', { method: 'PUT', body: req, token })
}

export function readStoredProfile(token: string): Promise<ProfileRequest> {
  return apiRequest('/v1/profile/stored', { token })
}
