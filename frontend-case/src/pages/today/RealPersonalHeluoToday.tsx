import { useCallback, useEffect, useRef, useState } from 'react'
import { fetchPersonalHeluoToday, type HeluoTodayResponse } from '../../api/heluoToday'
import { ApiClientError } from '../../api/http'
import ErrorState from '../../components/feedback/ErrorState'
import LoadingState from '../../components/feedback/LoadingState'
import './RealPersonalHeluoToday.css'

interface Props { token: string; onSessionExpired?: () => void; onProfileRequired?: () => void }

function validDate(value: unknown): value is string {
  if (typeof value !== 'string' || !/^\d{4}-\d{2}-\d{2}$/.test(value)) return false
  const parsed = new Date(`${value}T00:00:00Z`)
  return !Number.isNaN(parsed.getTime()) && parsed.toISOString().slice(0, 10) === value
}

/** 个人河洛五日一爻：后端给什么就展示什么，不在前端起卦或推周期。 */
export default function RealPersonalHeluoToday({ token, onSessionExpired, onProfileRequired }: Props) {
  const [view, setView] = useState<HeluoTodayResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [failed, setFailed] = useState(false)
  const [profileMissing, setProfileMissing] = useState(false)
  const [ambiguousLocation, setAmbiguousLocation] = useState(false)
  const requestGeneration = useRef(0)

  const load = useCallback(async () => {
    const generation = ++requestGeneration.current
    setLoading(true); setFailed(false); setProfileMissing(false); setAmbiguousLocation(false); setView(null)
    try {
      const result = await fetchPersonalHeluoToday(token)
      if (generation !== requestGeneration.current) return
      if (result.source !== 'heluo_timeline_liuri' || result.period_days !== 5 ||
          typeof result.hexagram !== 'string' || !result.hexagram ||
          !validDate(result.date) || !validDate(result.period_start) || !validDate(result.period_end) ||
          result.date < result.period_start || result.date > result.period_end ||
          (result.upper != null && typeof result.upper !== 'string') ||
          (result.lower != null && typeof result.lower !== 'string') ||
          !Array.isArray(result.lines) || result.lines.length !== 6 ||
          !result.lines.every(line => line === -1 || line === 0 || line === 1) ||
          !Number.isInteger(result.active_yao_index) || result.active_yao_index < 0 ||
          result.active_yao_index > 5) throw new Error('invalid heluo contract')
      setView(result)
    } catch (error) {
      if (generation !== requestGeneration.current) return
      if (error instanceof ApiClientError && error.status === 404 && error.normalized.code === 'PROFILE_NOT_FOUND') {
        setProfileMissing(true)
        return
      }
      if (error instanceof ApiClientError && error.status === 422 && error.normalized.code === 'PROFILE_LOCATION_AMBIGUOUS') {
        setAmbiguousLocation(true)
        return
      }
      setFailed(true)
      if (error instanceof ApiClientError && error.status === 401) onSessionExpired?.()
    }
    finally { if (generation === requestGeneration.current) setLoading(false) }
  }, [token, onSessionExpired])

  useEffect(() => {
    void load()
    return () => { requestGeneration.current += 1 }
  }, [load])
  if (loading) return <LoadingState />
  if (ambiguousLocation) return <section className="page-container" role="status"><h1>请确认出生地</h1><p>档案中的地点有多个匹配，请重新选择城市并保存后查看。</p>{onProfileRequired && <button type="button" onClick={onProfileRequired}>确认出生地</button>}</section>
  if (profileMissing) return <section className="page-container" role="status"><h1>先完善出生资料</h1><p>保存资料后，才能查看个人今日信息。</p>{onProfileRequired && <button type="button" onClick={onProfileRequired}>填写出生资料</button>}</section>
  if (failed || !view) return <ErrorState type="calculation" onRetry={() => void load()} />
  return <section className="personal-today" aria-label="个人河洛今日">
    <span className="personal-today__eyebrow">PERSONAL TODAY / 个人今日</span>
    <h1>{view.hexagram}</h1>
    <p className="personal-today__date">{view.date} · {view.period_start} 至 {view.period_end}</p>
    <svg className="personal-today__hexagram" viewBox="0 0 220 180" role="img" aria-label={`${view.hexagram}，当前第 ${view.active_yao_index + 1} 爻`}>
      {[...view.lines].reverse().map((line, visualIndex) => {
        const sourceIndex = 5 - visualIndex
        const active = sourceIndex === view.active_yao_index
        const y = 18 + visualIndex * 24
        return <g key={sourceIndex} className={active ? 'personal-today__line is-active' : 'personal-today__line'} data-yao={sourceIndex + 1}>
          {line === 1 ? <rect x="40" y={y} width="140" height="5" /> : <><rect x="40" y={y} width="62" height="5" /><rect x="118" y={y} width="62" height="5" /></>}
          {active && <circle cx="23" cy={y + 2.5} r="3" />}
        </g>
      })}
    </svg>
    <p className="personal-today__focus">当前第 {view.active_yao_index + 1} 爻</p>
    <p>上卦 {view.upper || '未提供'} · 下卦 {view.lower || '未提供'} · 每爻管五日</p>
    <p className="personal-today__note">此处展示河洛流日定位，个人解释和行动建议尚未开放。</p>
    <details><summary>查看来源</summary><p>{view.source} · trace: {view.trace_id}</p></details>
  </section>
}
