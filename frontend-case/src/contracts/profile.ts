/**
 * Contract Types — POST /v1/profile
 *
 * 依据：API_VIEW_CONTRACT.md §4（2026-11-11 实测）。
 * 注意：ProfileRequest 用嵌套 birth_time{hour,minute}，与 ReadingRequest 的扁平 hour 不同。
 */

export interface BirthTime {
  hour: number // 0-23
  minute?: number | null // 0-59，None = 时辰中点
}

export interface ProfileRequest {
  birth_date: string // YYYY-MM-DD
  birth_time: BirthTime
  gender: 'male' | 'female'
  timezone?: string | null
  calendar_system?: string | null
  location?: string | null
  current_location?: string | null
  analysis_date?: string | null
}

export interface BirthEffective {
  date: string
  hour: number
  minute: number
  day_rolled: boolean
}

export interface Corrections {
  utc_offset_min: number
  ref_meridian: number
  longitude: number
  longitude_correction_min: number
  eot_min: number
  total_correction_min: number
}

export interface ResolvedTimePolicy {
  timezone: string
  longitude: number
  latitude: number
  apparent_solar: boolean
  calendar_system: string
  day_boundary: string // "00:00"（晚子时裁决：00:00 换日）
  birth_effective: BirthEffective
  correction_minutes: number
  corrections: Corrections
  warnings: string[]
}

export type ProfileStatus = 'VALID' | 'INSUFFICIENT_INPUT'

export interface ProfileResponse {
  profile_status: ProfileStatus
  birth_date: string
  birth_time: BirthTime
  timezone: string
  location: string
  calendar_system: string
  resolved_time_policy: ResolvedTimePolicy
  trace_id: string
}
