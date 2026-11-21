import { useState } from 'react'
import { apiRequest, ApiClientError } from '../../api/http'
import hetu from '../../assets/product-b/hetu.svg?url'

type Preview = {
  date: string
  birth_timezone: string
  hexagram: string
  line: { index: number; engine_time_marker: string }
  rule: 'gua6'
  engine_version: string
  source: string
  marker_matches_requested_date: boolean
  current_line_status: 'pending_review'
}

export default function HeluoPreviewToday({ token, onAccount }: { token: string; onAccount: () => void }) {
  const [date, setDate] = useState('')
  const [result, setResult] = useState<Preview | null>(null)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  async function load() {
    setBusy(true)
    setError('')
    setResult(null)
    try {
      const data = await apiRequest<Preview>(`/v1/personal/heluo-preview?target_date=${encodeURIComponent(date)}`, { token })
      if (data?.date !== date || data.rule !== 'gua6' || data.current_line_status !== 'pending_review' ||
          typeof data.hexagram !== 'string' || !Number.isInteger(data.line?.index) ||
          data.line.index < 0 || data.line.index > 5 || typeof data.line.engine_time_marker !== 'string') {
        throw new Error('Invalid preview contract')
      }
      setResult(data)
    } catch (err) {
      setError(err instanceof ApiClientError && err.status === 401 ? 'Your session expired. Sign in again.' :
        err instanceof ApiClientError && err.normalized.code === 'PROFILE_NOT_FOUND' ? 'Save a birth profile to continue.' :
        err instanceof ApiClientError && err.status === 422 ? 'Review the date and the saved birth time.' :
        'The engine preview is unavailable. Try again.')
    } finally {
      setBusy(false)
    }
  }

  return <section className="page-container">
    <h1>Personal Today</h1>
    <p>Isolated test preview</p>
    <img src={hetu} alt="" width="128" height="128" />
    <form onSubmit={event => { event.preventDefault(); void load() }}>
      <label>Target date <input type="date" required disabled={busy} value={date}
        onChange={event => { setDate(event.target.value); setResult(null); setError('') }} /></label>
      <button type="submit" disabled={busy}>{busy ? 'Calculating…' : 'Calculate preview'}</button>
    </form>
    {error && <p role="alert">{error} <button onClick={onAccount}>Account and birth profile</button></p>}
    {result && <div role="status">
      <h2>{result.hexagram}</h2>
      <p>Engine-selected line {result.line.index + 1}</p>
      <p>Current active line and personal guidance await rule review.</p>
      {!result.marker_matches_requested_date && <p>The engine marker falls on a different calendar date.</p>}
      <details><summary>Calculation source</summary>
        <p>{result.source} · {result.engine_version} · {result.rule}</p>
        <p>Engine marker {result.line.engine_time_marker} (timezone unspecified by the engine)</p>
        <p>Saved birth timezone {result.birth_timezone}</p>
      </details>
    </div>}
  </section>
}
