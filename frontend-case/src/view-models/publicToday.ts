/**
 * View Model — Public Today（真数据模式）
 *
 * 数据源：GET /v1/today 游客态响应（contracts/today.ts TodayResponse）。
 * 规则（LIORIN_FRONTEND_SPEC_V2 §0/§红线）：
 * - 只做字段映射与文案格式化，不做任何命理计算/卦象推导/日期推导。
 * - 只消费 provenance 标注为 computed 的真数据字段；
 *   mock_until 字段（greeting/theme/hexagram/reasoning 等）不期待、不消费。
 * - daily_hexagram 后端当前只回 name/upper/lower/moving_line/changed，
 *   无 lines/symbol —— 前端不做卦象推导补齐，SVG 爻线留待后端契约扩展（见 Gap 登记）。
 */

import type { TodayResponse } from '../contracts/today'

/** 真数据公共今日卡视图模型 */
export interface RealPublicTodayView {
  /** e.g. "2026.11.12 · 丙午年 己亥月 庚辰日"（仅拼接 API 已有字符串） */
  dateLabel: string
  /** 卦名，e.g. "火水未济" */
  hexName: string
  /** 上卦名，e.g. "火" */
  hexUpper: string
  /** 下卦名，e.g. "水" */
  hexLower: string
  /** 动爻，e.g. "九三" */
  movingLine: string
  /** 变卦，e.g. "火风鼎" */
  changedHex: string
  /** 宜（真数据列表） */
  yi: string[]
  /** 忌（真数据列表） */
  ji: string[]
  /** 干支三柱展示（年/月/日，直接来自 API ganZhi） */
  pillars: { name: string; label: string; color: string }[]
  /** 黄历要点（全部为 API 字段直取） */
  essentials: { label: string; value: string }[]
  /** 农历月（API lunarMonth） */
  lunarMonth: string
  /** 星期（API weekday） */
  weekday: string
  /** 日期数字（API day） */
  day: number
  /** 溯源 */
  traceId: string
}

function formatPillarSuffix(ganzhi: string): string {
  // "丙午" -> "丙午年"：只追加年份后缀用于日期行，不拆解单字
  return `${ganzhi}年`
}

/**
 * TodayResponse → RealPublicTodayView
 * 缺字段 fail-fast 语义：daily_hexagram 缺 name 时抛错（契约破坏，不静默兜底）。
 */
export function buildRealPublicTodayView(resp: TodayResponse): RealPublicTodayView {
  const cal = resp.calendar
  const hex = cal.daily_hexagram
  if (!hex || !hex.name) {
    throw new Error('CONTRACT: calendar.daily_hexagram.name 缺失（契约破坏，FAIL FAST）')
  }

  const yearGz = cal.year_ganzhi
  const monthGz = cal.month_ganzhi
  const dayGz = cal.day_ganzhi
  const solar = cal.solar_date
  const dateLabel =
    solar && yearGz && monthGz && dayGz
      ? `${solar} · ${formatPillarSuffix(yearGz)} ${monthGz}月 ${dayGz}日`
      : solar || ''

  const essentials: RealPublicTodayView['essentials'] = []
  if (cal.lunar_month_label) essentials.push({ label: '农历', value: cal.lunar_month_label })
  if (cal.jie_qi) essentials.push({ label: '节气', value: cal.jie_qi })
  if (cal.jianchu) essentials.push({ label: '建除', value: cal.jianchu })
  if (cal.chong) {
    const v = cal.chong_shengxiao ? `${cal.chong}（${cal.chong_shengxiao}）` : cal.chong
    essentials.push({ label: '冲煞', value: v })
  }
  if (cal.nian_na_yin) essentials.push({ label: '年纳音', value: cal.nian_na_yin })
  if (cal.day_na_yin) essentials.push({ label: '日纳音', value: cal.day_na_yin })

  return {
    dateLabel,
    hexName: hex.name,
    hexUpper: hex.upper ?? '',
    hexLower: hex.lower ?? '',
    movingLine: hex.moving_line ?? '',
    changedHex: hex.changed ?? '',
    yi: Array.isArray(resp.yi) ? resp.yi : [],
    ji: Array.isArray(resp.ji) ? resp.ji : [],
    pillars: resp.ganZhi.map((p) => ({ name: p.name, label: p.label, color: p.color })),
    essentials,
    lunarMonth: resp.lunarMonth,
    weekday: resp.weekday,
    day: resp.day,
    traceId: resp.trace_id,
  }
}
