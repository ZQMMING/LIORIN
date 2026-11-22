import { useEffect, useState } from 'react'
import { apiRequest, ApiClientError } from '../api/http'
import { useProductLanguage } from '../productLanguage'
import './PersonalDnaPage.css'

const copy = {
  en: { title: 'Insight', language: 'Language', profile: 'Sign in and save a complete birth profile to view your cycles.',
    account: 'Open birth profile', year: 'Year', load: 'View cycles', loading: 'Calculating cycles…',
    error: 'Cycles could not be loaded. Try again.', annual: 'Annual cycle', months: 'Solar-term months',
    basis: 'Month numbers follow the solar-term calendar.', decade: 'Decadal cycle pending rule admission.',
    missing: 'Cycle data unavailable for this year.', source: 'Calculation source', reference: 'Calculation reference date',
    referencePurpose: 'This date selects the engine records for the requested year.',
    effective: 'Effective dates await rule approval.' },
  'zh-Hans': { title: '洞察', language: '语言', profile: '请登录并保存完整的出生档案，以查看周期。',
    account: '打开出生档案', year: '年份', load: '查看周期', loading: '正在计算周期…',
    error: '暂时无法加载周期，请重试。', annual: '年度周期', months: '节气月',
    basis: '月序采用节气历。', decade: '大运周期的规则尚待准入。',
    missing: '该年周期数据暂不可用。', source: '计算来源', reference: '计算参考日',
    referencePurpose: '参考日用于选择请求年份的引擎记录。', effective: '生效日期待规则审核。' },
  'zh-Hant': { title: '洞察', language: '語言', profile: '請登入並儲存完整的出生檔案，以查看週期。',
    account: '開啟出生檔案', year: '年份', load: '查看週期', loading: '正在計算週期…',
    error: '暫時無法載入週期，請重試。', annual: '年度週期', months: '節氣月',
    basis: '月序採用節氣曆。', decade: '大運週期的規則尚待准入。',
    missing: '該年週期資料暫不可用。', source: '計算來源', reference: '計算參考日',
    referencePurpose: '參考日用於選擇請求年份的引擎記錄。', effective: '生效日期待規則審核。' },
}

type Insight = {
  requested_year: number
  annual: { ganzhi: string; hexagram: string } | null
  solar_months: { index: number; hexagram: string }[]
  decadal_status: 'pending_ziping_admission'
  interpretation_status: 'pending_content_admission'
  source: { adapter: string; reference_date: string; heluo_version: string; bazi_version: string; calendar_version: string;
    month_basis: 'solar_term_month_ordinal' }
}

export default function PersonalInsightPage({ token, onAccount, onSessionExpired }: {
  token: string | null; onAccount: () => void; onSessionExpired: () => void
}) {
  const sharedLanguage = useProductLanguage()
  const [localLanguage, setLanguage] = useState<keyof typeof copy>('en')
  const language = sharedLanguage?.locale ?? localLanguage
  const [year, setYear] = useState('')
  const [selection, setSelection] = useState<{ year: number } | null>(null)
  const [state, setState] = useState<'idle' | 'loading' | 'profile' | 'error' | 'ready'>('idle')
  const [result, setResult] = useState<Insight | null>(null)
  const labels = copy[language]

  useEffect(() => {
    if (!token || !selection) return
    const controller = new AbortController()
    apiRequest<Insight>(`/v1/personal/insight?year=${selection.year}`, { token, signal: controller.signal })
      .then(data => {
        if (controller.signal.aborted) return
        if (data?.requested_year !== selection.year || data.decadal_status !== 'pending_ziping_admission' ||
            data.interpretation_status !== 'pending_content_admission' || !data.source ||
            data.source.month_basis !== 'solar_term_month_ordinal' ||
            !['adapter', 'reference_date', 'heluo_version', 'bazi_version', 'calendar_version'].every(
              key => typeof data.source[key as keyof Insight['source']] === 'string',
            ) || (data.annual !== null && (typeof data.annual?.ganzhi !== 'string' ||
                typeof data.annual.hexagram !== 'string')) || !Array.isArray(data.solar_months) ||
            (data.solar_months.length !== 0 && data.solar_months.length !== 12) ||
            !data.solar_months.every((item, index) => item?.index === index + 1 && typeof item.hexagram === 'string')) {
          throw new Error('Invalid cycle response')
        }
        setResult(data)
        setState('ready')
      }).catch(error => {
        if (controller.signal.aborted) return
        if (error instanceof ApiClientError && error.status === 401) onSessionExpired()
        setState(error instanceof ApiClientError &&
          (error.status === 422 || error.normalized.code === 'PROFILE_NOT_FOUND') ? 'profile' : 'error')
      })
    return () => controller.abort()
  }, [token, selection, onSessionExpired])

  return <section className="page-container personal-dna" lang={language}>
    <header className="personal-dna__header">
      <h1>{labels.title}</h1>
      {!sharedLanguage && <label>{labels.language} <select value={language} onChange={event => setLanguage(event.target.value as keyof typeof copy)}>
        <option value="en">English</option><option value="zh-Hans">简体中文</option><option value="zh-Hant">繁體中文</option>
      </select></label>}
    </header>
    {token && <form className="personal-insight__year" onSubmit={event => {
      event.preventDefault()
      setState('loading')
      setResult(null)
      setSelection({ year: Number(year) })
    }}>
      <label>{labels.year} <input type="number" min="1" max="9999" required value={year}
        disabled={state === 'loading'} onChange={event => { setYear(event.target.value); setResult(null); setState('idle') }} /></label>
      <button type="submit" disabled={state === 'loading'}>{labels.load}</button>
    </form>}
    {(!token || state === 'profile') && <><p role="status">{labels.profile}</p><button type="button" onClick={onAccount}>{labels.account}</button></>}
    {token && state === 'loading' && <p role="status">{labels.loading}</p>}
    {token && state === 'error' && <p role="alert">{labels.error}</p>}
    {token && state === 'ready' && result && <>
      <section className="personal-dna__nayin">
        <h2>{labels.annual} · {result.requested_year}</h2>
        {result.annual ? <p lang="zh">{result.annual.ganzhi} · {result.annual.hexagram}</p> : <p>{labels.missing}</p>}
      </section>
      <h2>{labels.months}</h2>
      {result.solar_months.length > 0 ? <><p>{labels.basis}</p>
        <ol className="personal-dna__pillars personal-insight__months">{result.solar_months.map(month => <li key={month.index} lang="zh">{month.hexagram}</li>)}</ol>
      </> : <p>{labels.missing}</p>}
      <p>{labels.decade}</p>
      <details><summary>{labels.source}</summary>
        <p>{labels.reference} · {result.source.reference_date}</p>
        <p>{labels.referencePurpose}</p>
        <p>{labels.effective}</p>
        <p>{result.source.adapter} · {result.source.heluo_version}</p>
        <p>{result.source.bazi_version} · sxtwl {result.source.calendar_version}</p>
      </details>
    </>}
  </section>
}
