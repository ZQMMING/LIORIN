/**
 * Contract Types — GET /v1/today
 *
 * 依据：frontend-case/contracts/API_VIEW_CONTRACT.md §3（2026-11-11 实测）。
 * 只收录后端真实返回的字段。mock_until 字段（greeting/theme/hexagram/reasoning 等）
 * 实际无数据，不在此声明。字段分类遵循 provenance 实测口径。
 */

/** 年/月/日柱干支（当日） */
export interface GanZhiPillar {
  name: string // e.g. "丙午"
  label: string // "年柱" | "月柱" | "日柱"
  color: string // CSS var, e.g. "var(--c-huo)"
}

export interface JieQi {
  name: string
  date: string
}

export interface DailyHexagram {
  name: string // e.g. "天雷无妄"
  upper: string
  lower: string
  moving_line: string
  changed: string
}

/** 完整黄历（36 字段，全部 computed） */
export interface CalendarData {
  solar_date: string
  day_stem: string
  day_branch: string
  year_ganzhi: string
  month_ganzhi: string
  day_ganzhi: string
  lunar_month: string
  lunar_day: string
  lunar_month_label: string
  jie_qi: string
  prev_jie_qi: JieQi
  next_jie_qi: JieQi
  jianchu: string
  zhishen: string
  zhishen_type: string
  zhishen_luck: string
  xiushu: string
  xiushu_luck: string
  chong: string
  chong_shengxiao: string
  sha: string
  sheng_xiao: string
  nian_na_yin: string
  month_na_yin: string
  day_na_yin: string
  peng_zu_gan: string
  peng_zu_zhi: string
  position_xi: string
  position_fu: string
  position_cai: string
  daily_hexagram: DailyHexagram
  yi: string[]
  ji: string[]
  ji_xiang: string[]
  xiong_sha: string[]
  source_ids: string[]
}

export interface TodayProvenance {
  ganZhi: string
  weekday: string
  day: string
  'lunarMonth/yi/ji/calendar': string
  'greeting/monthLabel/theme/catalyst/dimensions/time_window/hexagram/reasoning/cross_validation': string
}

/** 认证态才出现的 personal 块 */
export interface PersonalBlock {
  tier: 'personal'
  user_id?: string
  token_version?: number
  has_birth_info?: boolean
  is_new_user?: boolean
  device_id?: string
  device_type?: string
}

/** GET /v1/today 完整响应 */
export interface TodayResponse {
  ganZhi: GanZhiPillar[]
  weekday: string
  day: number
  lunarMonth: string
  yi: string[]
  ji: string[]
  calendar: CalendarData
  provenance: TodayProvenance
  trace_id: string
  personal?: PersonalBlock
}
