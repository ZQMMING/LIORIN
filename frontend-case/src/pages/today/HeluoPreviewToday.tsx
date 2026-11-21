import { useState } from 'react'
import { apiRequest, ApiClientError } from '../../api/http'
import hetu from '../../assets/product-b/hetu.svg?url'
import './HeluoPreviewToday.css'

type Preview = {
  requested_local_date: string
  display_timezone: string
  birth_timezone: string
  hexagram: string
  engine_selected_yao_index: number
  calendar_rule_id: 'gua6'
  engine_version: string
  engine_time_marker: string
  marker_timezone: null
  marker_utc: null
  active_yao_index: null
  valid_from: null
  valid_until: null
  provenance: { adapter: string; jie_start_marker: string; next_jie_marker: string; engine_day_ordinal: number }
  marker_matches_requested_date: boolean
  admission_status: 'pending_review'
}

export default function HeluoPreviewToday({ token, onAccount }: { token: string; onAccount: () => void }) {
  const [date, setDate] = useState('')
  const [displayZone, setDisplayZone] = useState(() => Intl.DateTimeFormat().resolvedOptions().timeZone)
  const [paused, setPaused] = useState(false)
  const [result, setResult] = useState<Preview | null>(null)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  async function load() {
    setBusy(true)
    setError('')
    setResult(null)
    try {
      const query = new URLSearchParams({target_date: date, display_timezone: displayZone})
      const data = await apiRequest<Preview>(`/v1/personal/heluo-preview?${query}`, { token })
      if (data?.requested_local_date !== date || data.display_timezone !== displayZone ||
          data.calendar_rule_id !== 'gua6' || data.admission_status !== 'pending_review' ||
          data.active_yao_index !== null || data.valid_from !== null || data.valid_until !== null ||
          data.marker_timezone !== null || data.marker_utc !== null || !data.provenance ||
          typeof data.hexagram !== 'string' || !Number.isInteger(data.engine_selected_yao_index) ||
          data.engine_selected_yao_index < 0 || data.engine_selected_yao_index > 5 ||
          typeof data.engine_time_marker !== 'string') {
        throw new Error('Invalid preview contract')
      }
      setResult(data)
    } catch (err) {
      setError(err instanceof ApiClientError && err.status === 401 ? 'Your session expired. Sign in again.' :
        err instanceof ApiClientError && err.normalized.code === 'PROFILE_NOT_FOUND' ? 'Save a birth profile to continue.' :
        err instanceof ApiClientError && err.status === 422 ? 'Review the date, display timezone and saved birth time.' :
        'The engine preview is unavailable. Try again.')
    } finally {
      setBusy(false)
    }
  }

  return <section className="page-container">
    <h1>Personal Today</h1>
    <p>Isolated test preview</p>
    <div className="preview-hetu" data-paused={paused}><img src={hetu} alt="" width="128" height="128" /></div>
    <button className="preview-motion-control" type="button" onClick={() => setPaused(value => !value)}>
      {paused ? 'Resume motion' : 'Pause motion'}
    </button>
    <form onSubmit={event => { event.preventDefault(); void load() }}>
      <label>Target date <input type="date" required disabled={busy} value={date}
        onChange={event => { setDate(event.target.value); setResult(null); setError('') }} /></label>
      <label>Display timezone <input required disabled={busy} value={displayZone}
        onChange={event => { setDisplayZone(event.target.value); setResult(null); setError('') }} /></label>
      <button type="submit" disabled={busy}>{busy ? 'Calculating…' : 'Calculate preview'}</button>
    </form>
    {error && <p role="alert">{error} <button onClick={onAccount}>Account and birth profile</button></p>}
    {result && <div role="status">
      <h2>{result.hexagram}</h2>
      <p>Engine-selected line {result.engine_selected_yao_index + 1}</p>
      <p>Current active line, validity window and guidance await review.</p>
      {!result.marker_matches_requested_date && <p>The raw marker shows a different calendar date from your request.</p>}
      <details><summary>Calculation source</summary>
        <p>{result.provenance.adapter} · {result.engine_version} · {result.calendar_rule_id}</p>
        <p>Requested date {result.requested_local_date} · display timezone {result.display_timezone}</p>
        <p>Engine marker {result.engine_time_marker} (timezone unverified)</p>
        <p>Solar-term markers {result.provenance.jie_start_marker} to {result.provenance.next_jie_marker}</p>
        <p>Calendar day ordinal {result.provenance.engine_day_ordinal}</p>
        <p>Saved birth timezone {result.birth_timezone}</p>
      </details>
    </div>}
  </section>
}
