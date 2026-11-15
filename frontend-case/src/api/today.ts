/**
 * Today API client — GET /v1/today
 *
 * 只消费 API_VIEW_CONTRACT.md §3 声明的真数据字段。
 * 不做前端推导、不填补 mock 字段。缺端点即返回空/错误，不 fallback 到 mock。
 */

import { apiRequest } from './http'
import type { TodayResponse } from '../contracts/today'

/** 拉取指定日期（或今天）的公共今日卡 */
export async function fetchToday(dateStr?: string, region = 'Beijing'): Promise<TodayResponse> {
  const qs = new URLSearchParams()
  if (dateStr) qs.set('date', dateStr)
  qs.set('region', region)
  return apiRequest<TodayResponse>(`/v1/today?${qs.toString()}`)
}
