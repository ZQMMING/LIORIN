import { useEffect, useState } from 'react'
import { InvalidEngineQaResponse, runEngineQa, type EngineQaResponse } from '../api/engineQa'
import { ApiClientError } from '../api/http'
import { fetchBirthLocations, type BirthLocation } from '../api/locations'
import BirthLocationPicker from '../components/account/BirthLocationPicker'
import './support-pages.css'
import './engine-qa.css'

function localToday(): string {
  const now = new Date()
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`
}

function qaErrorMessage(error: unknown): string {
  if (error instanceof InvalidEngineQaResponse) return '计算服务返回的数据不完整，本次结果无法展示。'
  if (!(error instanceof ApiClientError)) return '暂时无法连接测试服务或计算失败，请检查本机后端后重试。'
  const fields = new Set((error.normalized.details ?? []).flatMap(item => [item.field, ...(item.loc ?? [])]))
  if (fields.has('location')) return '出生地无法识别，请重新搜索并选择城市。'
  if (fields.has('timezone')) return '时区无法识别，请检查出生地或时区名称。'
  if (fields.has('birth_date') || fields.has('analysis_date')) return '日期未通过检查，请确认出生日期和分析日期。'
  if (error.status === 400 || error.status === 422) return '资料未通过检查，请确认出生日期、时间、性别和地点。'
  if (error.status === 404 || error.status === 503) return '本机测试服务暂不可用，请检查后端是否以测试模式启动。'
  return '本次计算未完成，请稍后重试。'
}

/** 本机引擎 QA 工作台：生产页面不可见；不保存出生资料。 */
export default function EngineQaPage() {
  const [birthDate, setBirthDate] = useState('')
  const [hour, setHour] = useState('')
  const [minute, setMinute] = useState('')
  const [gender, setGender] = useState<'male' | 'female' | ''>('')
  const [analysisDate, setAnalysisDate] = useState(localToday)
  const [timezone, setTimezone] = useState('')
  const [location, setLocation] = useState('')
  const [locationReset, setLocationReset] = useState(0)
  const [locations, setLocations] = useState<BirthLocation[]>([])
  const [locationsPending, setLocationsPending] = useState(true)
  const [locationsAttempt, setLocationsAttempt] = useState(0)
  useEffect(() => {
    let active = true
    setLocationsPending(true)
    void fetchBirthLocations().then(items => { if (active) setLocations(items) }).catch(() => { if (active) setLocations([]) }).finally(() => { if (active) setLocationsPending(false) })
    return () => { active = false }
  }, [locationsAttempt])
  const [theme, setTheme] = useState('WORK')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [result, setResult] = useState<EngineQaResponse | null>(null)
  const [copyStatus, setCopyStatus] = useState('')

  return <main className="support-page engine-qa" aria-label="引擎测试工作台">
    <header className="support-header">
      <span className="support-eyebrow">TEST ONLY / 本机测试</span>
      <h1>引擎问题排查。</h1>
      <p>本页使用本机 QA 测试会话（非正式用户账号），无需登录。输入测试命例后调用生产计算管线，返回有界摘要、证据数量与 trace；不保存出生资料，不代表算法已验收。</p>
    </header>
    <div className="engine-qa-actions">
      <button type="button" disabled={busy} onClick={() => {
        setBirthDate('1980-06-22'); setHour('12'); setMinute('30')
        setGender('male'); setAnalysisDate('2026-08-17')
        setTimezone('Asia/Shanghai'); setLocation('CN_BEIJING'); setTheme('WORK')
        setLocationReset(n => n + 1)
        setResult(null); setError('')
      }}>载入测试命例（不自动提交）</button>
      <button type="button" disabled={busy} onClick={() => {
        setBirthDate(''); setHour(''); setMinute(''); setGender(''); setAnalysisDate(''); setTimezone(''); setLocation('')
        setLocationReset(n => n + 1)
        setResult(null); setError(''); setCopyStatus('')
      }}>清空输入与结果</button>
    </div>
    <form onChange={() => { setResult(null); setError(''); setCopyStatus('') }} onSubmit={event => { event.preventDefault(); setBusy(true); setError(''); setResult(null)
      if (!gender || minute === '') { setBusy(false); setError('请填写出生分钟并选择性别。'); return }
      void runEngineQa({
        birth_date: birthDate, hour: Number(hour),
        birth_minute: Number(minute),
        gender, analysis_date: analysisDate, timezone, location, theme,
      }).then(setResult).catch(e => setError(qaErrorMessage(e)))
        .finally(() => setBusy(false))
    }}>
      <fieldset disabled={busy}>
      <label>出生日期<input required type="date" value={birthDate} onChange={e => setBirthDate(e.target.value)} /></label>
      <label>出生时间<input required type="time" value={hour !== '' && minute !== '' ? `${hour.padStart(2, '0')}:${minute.padStart(2, '0')}` : ''} onChange={e => {
        const [h, m] = e.target.value ? e.target.value.split(':') : ['', '']
        setHour(h); setMinute(m)
      }} /></label>
      <label>性别<select required value={gender} onChange={e => setGender(e.target.value as 'male' | 'female' | '')}><option value="">请选择</option><option value="male">男</option><option value="female">女</option></select></label>
      <label>分析日期<input required type="date" value={analysisDate} onChange={e => setAnalysisDate(e.target.value)} /></label>
      <label>时区<input required placeholder="例如 Asia/Shanghai" value={timezone} onChange={e => setTimezone(e.target.value)} /></label>
      <BirthLocationPicker key={locationReset} loading={locationsPending} onRetry={() => setLocationsAttempt(n => n + 1)} locations={locations} value={location} onChange={value => {
        setLocation(value)
        const selected = locations.find(city => city.id === value)
        if (selected?.timezone) setTimezone(selected.timezone)
        else if (locations.length) setTimezone('')
      }} />
      <label>主题<input required value={theme} onChange={e => setTheme(e.target.value)} /></label>
      <button type="submit" disabled={busy || locationsPending || !locations.some(city => city.id === location)}>{busy ? '正在计算…' : '运行引擎测试'}</button>
      </fieldset>
    </form>
    {error && <p role="alert">{error}</p>}
    {result && <section role="status" aria-label="引擎测试结果">
      <h2>本次计算结果</h2>
      <p>{result.warning}</p>
      <p>文本校验：{result.validation_status === 'not_run' ? '未执行（本次仅计算）' : '状态未知'} · 来源：{result.source}</p>
      {result.bazi_pillars && <div className="qa-result-overview qa-bazi" aria-label="八字四柱">
        {(['year', 'month', 'day', 'hour'] as const).map((key, index) => <div key={key}>
          <span>{['年柱', '月柱', '日柱', '时柱'][index]}</span><strong>{result.bazi_pillars?.[key] || '暂无'}</strong>
        </div>)}
      </div>}
      <div className="qa-result-overview" aria-label="河洛计算结果">
        <div><span>先天卦</span><strong>{result.heluo?.prenatal || '暂无结果'}</strong></div>
        <div><span>后天卦</span><strong>{result.heluo?.postnatal || '暂无结果'}</strong></div>
      </div>
      <p>以上为测试管线返回的结构信息；尚未经过文本校验或算法验收，不应作为已验收的个人结论。</p>
      <details className="qa-technical-details">
      <summary>查看计算详情与证据</summary>
      <p>canonical: {result.canonical_id} · trace: {result.trace_id || '未返回'}</p>
      <button type="button" onClick={() => void navigator.clipboard.writeText(JSON.stringify(result, null, 2))
        .then(() => setCopyStatus('已复制摘要，可附在问题反馈中。'))
        .catch(() => setCopyStatus('复制失败；请使用页面上的 canonical/trace 编号反馈。'))}>复制问题摘要 JSON</button>
      {copyStatus && <p role="status">{copyStatus}</p>}
      <p>河洛结果：{result.result_available.heluo ? '有' : '无'} · 易经结构：{result.result_available.yijing_structure ? '有' : '无'} · 子平 claims：{result.ziping_claim_count}</p>
      <h3>按引擎观察到的证据条数</h3>
      <ul>{Object.entries(result.observed_evidence_by_engine).map(([engine, count]) => <li key={engine}>{engine}：{count}</li>)}</ul>
      <h3>结论与证据索引（最多 50 条）</h3>
      <ul>{result.claims.map((c, i) => <li key={c.claim_id || i}>
        <strong>{c.domain || c.claim_id || '未分类'}</strong> · {c.conclusion || '未定'}<br />
        {c.claim}<br /><small>证据：{c.evidence_refs.join('、') || '未提供'}</small>
      </li>)}</ul>
      </details>
    </section>}
  </main>
}
