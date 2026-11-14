import { apiRequest } from './http'

export interface HeluoTodayResponse {
  date: string
  hexagram: string
  upper: string | null
  lower: string | null
  lines: number[]
  active_yao_index: number // 后端 0-5；前端仅展示，不自行推断
  period_start: string
  period_end: string
  period_days: 5
  source: 'heluo_timeline_liuri'
  trace_id: string
}

export function fetchPersonalHeluoToday(token: string, dateStr?: string): Promise<HeluoTodayResponse> {
  const qs = dateStr ? `?date=${encodeURIComponent(dateStr)}` : ''
  return apiRequest<HeluoTodayResponse>(`/v1/personal/heluo-today${qs}`, { token })
}
