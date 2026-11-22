import { useEffect, useState } from 'react'
import { apiRequest, ApiClientError } from '../api/http'
import './PersonalDnaPage.css'

const copy = {
  en: {
    title: 'Personal DNA', language: 'Language', signIn: 'Sign in to view your Personal DNA.',
    profile: 'Save a birth profile to see your Personal DNA.', edit: 'Open birth profile',
    uncertain: 'A complete, unambiguous birth time is required.',
    loading: 'Calculating your birth chart…', unavailable: 'Personal DNA is unavailable.', retry: 'Retry',
    nayin: 'Birth-year Na Yin', master: 'Day master', chart: 'Four pillars',
    stem: 'Stem', branch: 'Branch', source: 'Calculation source', timezone: 'Birth timezone',
    zodiac: 'Birth zodiac unavailable · year boundary under review.',
    positions: ['Year', 'Month', 'Day', 'Hour'], elements: ['Wood', 'Fire', 'Earth', 'Metal', 'Water'],
  },
  'zh-Hans': {
    title: '个人图谱', language: '语言', signIn: '请登录后查看个人图谱。',
    profile: '请先保存出生资料。', edit: '打开出生档案', uncertain: '需要填写完整且无歧义的出生时间。',
    loading: '正在计算出生四柱…', unavailable: '个人图谱暂不可用。', retry: '重试',
    nayin: '出生年纳音', master: '日主', chart: '四柱', stem: '天干', branch: '地支',
    source: '计算来源', timezone: '出生时区', zodiac: '出生生肖暂不可用 · 年界待审核。',
    positions: ['年柱', '月柱', '日柱', '时柱'], elements: ['木', '火', '土', '金', '水'],
  },
  'zh-Hant': {
    title: '個人圖譜', language: '語言', signIn: '請登入後查看個人圖譜。',
    profile: '請先儲存出生資料。', edit: '開啟出生檔案', uncertain: '需要填寫完整且無歧義的出生時間。',
    loading: '正在計算出生四柱…', unavailable: '個人圖譜暫不可用。', retry: '重試',
    nayin: '出生年納音', master: '日主', chart: '四柱', stem: '天干', branch: '地支',
    source: '計算來源', timezone: '出生時區', zodiac: '出生生肖暫不可用 · 年界待審核。',
    positions: ['年柱', '月柱', '日柱', '時柱'], elements: ['木', '火', '土', '金', '水'],
  },
}

const elements = ['WOOD', 'FIRE', 'EARTH', 'METAL', 'WATER']
const positions = ['year', 'month', 'day', 'hour']

type Dna = {
  birth_year_nayin: string
  day_master: string
  day_master_element: string
  pillars: { position: string; name: string; stem_element: string; branch_element: string }[]
  zodiac_status: 'pending_year_boundary_review'
  source: { chain: string; engine_version: string; calculation_version: string; package_version: string;
    calendar_version: string; birth_timezone: string }
}
type State = { status: 'loading' | 'missing' | 'uncertain' | 'error' } | { status: 'ready'; data: Dna }

export default function PersonalDnaPage({ token, onAccount, onSessionExpired }: {
  token: string | null; onAccount: () => void; onSessionExpired: () => void
}) {
  const [locale, setLocale] = useState<keyof typeof copy>('en')
  const [state, setState] = useState<State>({ status: 'loading' })
  const [attempt, setAttempt] = useState(0)
  const labels = copy[locale]

  useEffect(() => {
    if (!token) return
    const controller = new AbortController()
    apiRequest<Dna>('/v1/personal/dna', { token, signal: controller.signal }).then(data => {
      if (controller.signal.aborted) return
      if (typeof data?.birth_year_nayin !== 'string' || typeof data.day_master !== 'string' ||
          !elements.includes(data.day_master_element) || data.zodiac_status !== 'pending_year_boundary_review' ||
          !data.source || !['chain', 'engine_version', 'calculation_version', 'package_version',
            'calendar_version', 'birth_timezone'].every(key => typeof data.source[key as keyof Dna['source']] === 'string') ||
          !Array.isArray(data.pillars) || data.pillars.length !== positions.length ||
          !data.pillars.every((pillar, index) => pillar?.position === positions[index] &&
            typeof pillar.name === 'string' && elements.includes(pillar.stem_element) && elements.includes(pillar.branch_element))) {
        throw new Error('Invalid Personal DNA response')
      }
      setState({ status: 'ready', data })
    }).catch(error => {
      if (controller.signal.aborted) return
      if (error instanceof ApiClientError && error.status === 401) onSessionExpired()
      setState({ status: error instanceof ApiClientError && error.normalized.code === 'PROFILE_NOT_FOUND'
        ? 'missing' : error instanceof ApiClientError && error.status === 422 ? 'uncertain' : 'error' })
    })
    return () => controller.abort()
  }, [token, onSessionExpired, attempt])

  const element = (value: string) => labels.elements[elements.indexOf(value)]
  return <section className="page-container personal-dna" lang={locale}>
    <header className="personal-dna__header">
      <h1>{labels.title}</h1>
      <label>{labels.language} <select value={locale} onChange={event => setLocale(event.target.value as keyof typeof copy)}>
        <option value="en">English</option><option value="zh-Hans">简体中文</option><option value="zh-Hant">繁體中文</option>
      </select></label>
    </header>
    {(!token || state.status === 'missing' || state.status === 'uncertain') && <>
      <p role="status">{!token ? labels.signIn : state.status === 'missing' ? labels.profile : labels.uncertain}</p>
      <button type="button" onClick={onAccount}>{labels.edit}</button>
    </>}
    {token && state.status === 'loading' && <p role="status">{labels.loading}</p>}
    {token && state.status === 'error' && <div role="alert"><p>{labels.unavailable}</p>
      <button type="button" onClick={() => { setState({ status: 'loading' }); setAttempt(value => value + 1) }}>{labels.retry}</button>
    </div>}
    {token && state.status === 'ready' && <>
      <dl className="personal-dna__facts">
        <div><dt>{labels.nayin}</dt><dd lang="zh">{state.data.birth_year_nayin}</dd></div>
        <div><dt>{labels.master}</dt><dd><span lang="zh">{state.data.day_master}</span> · {element(state.data.day_master_element)}</dd></div>
      </dl>
      <h2>{labels.chart}</h2>
      <dl className="personal-dna__pillars">
        {state.data.pillars.map((pillar, index) => <div key={pillar.position}>
          <dt>{labels.positions[index]}</dt>
          <dd><strong lang="zh">{pillar.name}</strong>
            <span>{labels.stem} · {element(pillar.stem_element)}</span>
            <span>{labels.branch} · {element(pillar.branch_element)}</span>
          </dd>
        </div>)}
      </dl>
      <p>{labels.zodiac}</p>
      <details><summary>{labels.source}</summary>
        <p>{state.data.source.chain}</p>
        <p>{state.data.source.engine_version} · {state.data.source.calculation_version}</p>
        <p>heluo-engine {state.data.source.package_version} · sxtwl {state.data.source.calendar_version}</p>
        <p>{labels.timezone} · {state.data.source.birth_timezone}</p>
      </details>
    </>}
  </section>
}
