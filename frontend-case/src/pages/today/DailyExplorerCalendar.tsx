import { useEffect, useState } from 'react'
import { apiRequest } from '../../api/http'

const messages = {
  en: {
    title: 'Daily calendar', language: 'Language', loading: 'Loading calendar…', error: 'Calendar unavailable.',
    retry: 'Retry calendar', lunar: 'Lunar date', source: 'Calendar source',
    sections: ['Wealth, Joy and Blessing directions', 'Zodiac connections', 'Traditional time windows'],
    pending: 'Unavailable · source review pending', basis: 'Calculated for the selected Gregorian date.',
    zone: 'Display timezone', branch: 'Day branch', branchUnavailable: 'Day branch unavailable',
    branchSource: 'Day branch cross-check',
  },
  'zh-Hans': {
    title: '当日黄历', language: '语言', loading: '正在读取黄历…', error: '暂时无法读取黄历。',
    retry: '重试黄历', lunar: '农历', source: '黄历来源',
    sections: ['财神、喜神、福神方位', '生肖关系', '十二传统时辰'],
    pending: '暂不可用 · 来源待审核', basis: '按所选公历日期计算。', zone: '显示时区',
    branch: '当日地支', branchUnavailable: '当日地支暂不可用', branchSource: '地支复核',
  },
  'zh-Hant': {
    title: '當日黃曆', language: '語言', loading: '正在讀取黃曆…', error: '暫時無法讀取黃曆。',
    retry: '重試黃曆', lunar: '農曆', source: '黃曆來源',
    sections: ['財神、喜神、福神方位', '生肖關係', '十二傳統時辰'],
    pending: '暫不可用 · 來源待審核', basis: '按所選公曆日期計算。', zone: '顯示時區',
    branch: '當日地支', branchUnavailable: '當日地支暫不可用', branchSource: '地支複核',
  },
}

type Locale = keyof typeof messages
type Selection = { targetDate: string; displayTimezone: string }
type Calendar = {
  requested_local_date: string
  display_timezone: string
  lunar_date: string
  source: { id: 'lunar_python'; version: string; registry_version: string; date_basis: 'explicit_gregorian_date' }
  day_branch: { code: string; name: string; checked_with: 'sxtwl'; check_version: '2.0.7' } | null
  directions: PendingSection
  zodiac_connections: PendingSection
  time_windows: PendingSection
}
type PendingSection = { status: 'unavailable'; reason: 'field_admission_pending' }
type Loaded = { query: string; data: Calendar | null }

export default function DailyExplorerCalendar({ selection }: { selection: Selection | null }) {
  const { targetDate, displayTimezone } = selection ?? {}
  const [locale, setLocale] = useState<Locale>(() => {
    const language = navigator.language
    if (/^zh-(Hant|TW|HK|MO)/i.test(language)) return 'zh-Hant'
    return /^zh\b/i.test(language) ? 'zh-Hans' : 'en'
  })
  const [loaded, setLoaded] = useState<Loaded | null>(null)
  const [attempt, setAttempt] = useState(0)
  const labels = messages[locale]
  const query = targetDate && displayTimezone
    ? new URLSearchParams({ target_date: targetDate, display_timezone: displayTimezone }).toString()
    : ''

  useEffect(() => {
    if (!query) return
    const controller = new AbortController()
    apiRequest<Calendar>(`/v1/explorer/calendar?${query}`, { signal: controller.signal })
      .then(data => {
        if (controller.signal.aborted) return
        if (data?.requested_local_date !== targetDate || data.display_timezone !== displayTimezone ||
            typeof data.lunar_date !== 'string' || !data.lunar_date.trim() ||
            data.source?.id !== 'lunar_python' || typeof data.source.version !== 'string' ||
            typeof data.source.registry_version !== 'string' || data.source.date_basis !== 'explicit_gregorian_date' ||
            (data.day_branch !== null && (typeof data.day_branch?.code !== 'string' ||
              typeof data.day_branch.name !== 'string' || data.day_branch.checked_with !== 'sxtwl' ||
              data.day_branch.check_version !== '2.0.7')) ||
            ![data.directions, data.zodiac_connections, data.time_windows].every(
              item => item?.status === 'unavailable' && item.reason === 'field_admission_pending',
            )) throw new Error('Invalid calendar response')
        setLoaded({ query, data })
      })
      .catch(() => {
        if (!controller.signal.aborted) setLoaded({ query, data: null })
      })
    return () => controller.abort()
  }, [targetDate, displayTimezone, query, attempt])

  if (!query) return null
  const result = loaded?.query === query ? loaded : null
  return <section lang={locale} className="daily-explorer__calendar" aria-label={labels.title}>
    <h2>{labels.title}</h2>
    <label>{labels.language} <select value={locale} onChange={event => setLocale(event.target.value as Locale)}>
      <option value="en">English</option>
      <option value="zh-Hans">简体中文</option>
      <option value="zh-Hant">繁體中文</option>
    </select></label>
    {!result && <p role="status">{labels.loading}</p>}
    {result && !result.data && <p role="alert">{labels.error} <button type="button" onClick={() => {
      setLoaded(null)
      setAttempt(value => value + 1)
    }}>{labels.retry}</button></p>}
    {result?.data && <>
      <p role="status"><time dateTime={targetDate}>{targetDate}</time> · {labels.lunar} <span lang="zh">{result.data.lunar_date}</span></p>
      <p>{result.data.day_branch
        ? <><span>{labels.branch}</span> <span lang="zh">{result.data.day_branch.name}</span></>
        : labels.branchUnavailable}</p>
      <ul>{labels.sections.map(section => <li key={section}>{section} · {labels.pending}</li>)}</ul>
      <details><summary>{labels.source}</summary>
        <p>{labels.basis} {labels.zone} {displayTimezone}</p>
        <p>{result.data.source.id} {result.data.source.version} · calendar_sources.json {result.data.source.registry_version}</p>
        {result.data.day_branch && <p>{labels.branchSource} {result.data.day_branch.checked_with} {result.data.day_branch.check_version}</p>}
      </details>
    </>}
  </section>
}
