import { useState } from 'react'
import { apiRequest, ApiClientError } from '../../api/http'
import { useProductLanguage } from '../../productLanguage'
import hetu from '../../assets/product-b/hetu.svg?url'
import DailyExplorerCalendar from './DailyExplorerCalendar'
import './HeluoPreviewToday.css'

const copy = {
  en: { title: 'Personal Today', preview: 'Isolated test preview', pause: 'Pause motion', resume: 'Resume motion',
    explorer: 'Daily Explorer', target: 'Target date', zone: 'Display timezone', previous: 'Previous day', next: 'Next day',
    calculating: 'Calculating…', calculate: 'Calculate preview', account: 'Account and birth profile',
    session: 'Your session expired. Sign in again.', profile: 'Save a birth profile to continue.',
    invalid: 'Review the date, display timezone and saved birth time.', unavailable: 'The engine preview is unavailable. Try again.',
    line: 'Engine-selected line', pending: 'Current active line, validity window and guidance await review.',
    different: 'The raw marker shows a different calendar date from your request.', source: 'Calculation source',
    date: 'Requested date', marker: 'Engine marker', utc: 'Engine marker in UTC', solar: 'Solar-term markers',
    clock: 'Solar-term clock', fixed: 'fixed UTC+08:00, minute precision', unknown: 'time basis unverified',
    ordinal: 'Calendar day ordinal', birth: 'Saved birth timezone' },
  'zh-Hans': { title: '个人今日', preview: '隔离测试预览', pause: '暂停动效', resume: '恢复动效',
    explorer: '每日探索', target: '目标日期', zone: '显示时区', previous: '上一日', next: '下一日',
    calculating: '正在计算…', calculate: '计算预览', account: '账户与出生档案',
    session: '会话已过期，请重新登录。', profile: '请先保存出生档案。',
    invalid: '请核对日期、显示时区和出生时间。', unavailable: '计算预览暂不可用，请重试。',
    line: '引擎选中爻位', pending: '有效爻位、生效区间及指引待审核。',
    different: '引擎标记日期与请求日期不同。', source: '计算来源',
    date: '请求日期', marker: '引擎标记', utc: '引擎标记（UTC）', solar: '节气标记',
    clock: '节气计算时间', fixed: '固定 UTC+08:00，精确到分钟', unknown: '时间基准未核验',
    ordinal: '日序', birth: '档案出生时区' },
  'zh-Hant': { title: '個人今日', preview: '隔離測試預覽', pause: '暫停動效', resume: '恢復動效',
    explorer: '每日探索', target: '目標日期', zone: '顯示時區', previous: '上一日', next: '下一日',
    calculating: '正在計算…', calculate: '計算預覽', account: '帳戶與出生檔案',
    session: '工作階段已過期，請重新登入。', profile: '請先儲存出生檔案。',
    invalid: '請核對日期、顯示時區與出生時間。', unavailable: '計算預覽暫不可用，請重試。',
    line: '引擎選中爻位', pending: '有效爻位、生效區間及指引待審核。',
    different: '引擎標記日期與請求日期不同。', source: '計算來源',
    date: '請求日期', marker: '引擎標記', utc: '引擎標記（UTC）', solar: '節氣標記',
    clock: '節氣計算時間', fixed: '固定 UTC+08:00，精確到分鐘', unknown: '時間基準未核驗',
    ordinal: '日序', birth: '檔案出生時區' },
}

type Preview = {
  requested_local_date: string
  display_timezone: string
  birth_timezone: string
  hexagram: string
  engine_selected_yao_index: number
  calendar_rule_id: 'gua6'
  engine_version: string
  engine_time_marker: string
  marker_timezone: 'Asia/Shanghai' | '+08:00' | null
  marker_utc: string | null
  active_yao_index: null
  valid_from: null
  valid_until: null
  provenance: {
    adapter: string
    birth_time_basis: 'CalculationContext'
    solar_term_time_basis: 'sxtwl_jd2dd_fixed_utc_plus_08' | null
    sxtwl_version: string
    jie_start_marker: string
    next_jie_marker: string
    engine_day_ordinal: number
  }
  marker_matches_requested_date: boolean
  admission_status: 'pending_review'
}

function adjacentDate(day: string, delta: -1 | 1): string {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(day)) return ''
  const civilDate = new Date(`${day}T00:00:00Z`)
  if (!Number.isFinite(civilDate.getTime()) || civilDate.toISOString().slice(0, 10) !== day) return ''
  civilDate.setUTCDate(civilDate.getUTCDate() + delta)
  const year = civilDate.getUTCFullYear()
  return year > 0 && year <= 9999 ? civilDate.toISOString().slice(0, 10) : ''
}

export default function HeluoPreviewToday({ token, onAccount }: { token: string; onAccount: () => void }) {
  const locale = useProductLanguage()?.locale ?? 'en'
  const t = copy[locale]
  const [date, setDate] = useState('')
  const [displayZone, setDisplayZone] = useState(() => Intl.DateTimeFormat().resolvedOptions().timeZone)
  const [paused, setPaused] = useState(false)
  const [result, setResult] = useState<Preview | null>(null)
  const [error, setError] = useState<'' | 'session' | 'profile' | 'invalid' | 'unavailable'>('')
  const [busy, setBusy] = useState(false)
  const [calendarSelection, setCalendarSelection] = useState<{ targetDate: string; displayTimezone: string } | null>(null)

  const previousDate = adjacentDate(date, -1)
  const nextDate = adjacentDate(date, 1)

  async function load(targetDate: string) {
    setDate(targetDate)
    setCalendarSelection({ targetDate, displayTimezone: displayZone })
    setBusy(true)
    setError('')
    setResult(null)
    try {
      const query = new URLSearchParams({target_date: targetDate, display_timezone: displayZone})
      const data = await apiRequest<Preview>(`/v1/personal/heluo-preview?${query}`, { token })
      if (data?.requested_local_date !== targetDate || data.display_timezone !== displayZone ||
          data.calendar_rule_id !== 'gua6' || data.admission_status !== 'pending_review' ||
          data.active_yao_index !== null || data.valid_from !== null || data.valid_until !== null ||
          !data.provenance ||
          (data.marker_timezone === null
            ? data.marker_utc !== null || data.provenance.solar_term_time_basis !== null
            : !['Asia/Shanghai', '+08:00'].includes(data.marker_timezone) ||
              typeof data.marker_utc !== 'string' ||
              data.provenance.solar_term_time_basis !== 'sxtwl_jd2dd_fixed_utc_plus_08') ||
          typeof data.hexagram !== 'string' || !Number.isInteger(data.engine_selected_yao_index) ||
          data.engine_selected_yao_index < 0 || data.engine_selected_yao_index > 5 ||
          typeof data.engine_time_marker !== 'string') {
        throw new Error('Invalid preview contract')
      }
      setResult(data)
    } catch (err) {
      setError(err instanceof ApiClientError && err.status === 401 ? 'session' :
        err instanceof ApiClientError && err.normalized.code === 'PROFILE_NOT_FOUND' ? 'profile' :
        err instanceof ApiClientError && err.status === 422 ? 'invalid' : 'unavailable')
    } finally {
      setBusy(false)
    }
  }

  return <section className="page-container" lang={locale}>
    <h1>{t.title}</h1>
    <p>{t.preview}</p>
    <div className="preview-hetu" data-paused={paused}><img src={hetu} alt="" width="128" height="128" /></div>
    <button className="preview-motion-control" type="button" onClick={() => setPaused(value => !value)}>
      {paused ? t.resume : t.pause}
    </button>
    <form onSubmit={event => { event.preventDefault(); void load(date) }}>
      <fieldset className="daily-explorer">
        <legend>{t.explorer}</legend>
        <label>{t.target} <input type="date" required disabled={busy} value={date}
          onChange={event => { setDate(event.target.value); setResult(null); setError(''); setCalendarSelection(null) }} /></label>
        <label>{t.zone} <input required disabled={busy} value={displayZone}
          onChange={event => { setDisplayZone(event.target.value); setResult(null); setError(''); setCalendarSelection(null) }} /></label>
        <div className="daily-explorer__controls">
          <button type="button" disabled={busy || !previousDate || !displayZone.trim()}
            onClick={() => void load(previousDate)}>{t.previous}</button>
          <button type="submit" disabled={busy}>{busy ? t.calculating : t.calculate}</button>
          <button type="button" disabled={busy || !nextDate || !displayZone.trim()}
            onClick={() => void load(nextDate)}>{t.next}</button>
        </div>
      </fieldset>
    </form>
    <DailyExplorerCalendar selection={calendarSelection} />
    {error && <p role="alert">{t[error]} <button onClick={onAccount}>{t.account}</button></p>}
    {result && <div role="status">
      <h2>{result.hexagram}</h2>
      <p>{t.line} {result.engine_selected_yao_index + 1}</p>
      <p>{t.pending}</p>
      {!result.marker_matches_requested_date && <p>{t.different}</p>}
      <details><summary>{t.source}</summary>
        <p>{result.provenance.adapter} · {result.engine_version} · {result.calendar_rule_id}</p>
        <p>{t.date} {result.requested_local_date} · {t.zone} {result.display_timezone}</p>
        <p>{t.marker} {result.engine_time_marker} ({result.marker_timezone ?? t.unknown})</p>
        {result.marker_utc && <p>{t.utc} <time dateTime={result.marker_utc}>{result.marker_utc}</time></p>}
        <p>{t.solar} {result.provenance.jie_start_marker} – {result.provenance.next_jie_marker}</p>
        <p>{t.clock} sxtwl {result.provenance.sxtwl_version} · {result.provenance.solar_term_time_basis
          ? t.fixed : t.unknown}</p>
        <p>{t.ordinal} {result.provenance.engine_day_ordinal}</p>
        <p>{t.birth} {result.birth_timezone} · {result.provenance.birth_time_basis}</p>
      </details>
    </div>}
  </section>
}
