import { useEffect, useState } from 'react'
import type { BirthLocation } from '../../api/locations'

interface Props {
  locations: BirthLocation[]
  value: string
  onChange: (value: string) => void
  loading?: boolean
  onRetry?: () => void
}

export default function BirthLocationPicker({ locations, value, onChange, loading = false, onRetry }: Props) {
  const [query, setQuery] = useState(value)
  const [editing, setEditing] = useState(false)
  useEffect(() => {
    if (editing) return
    const selected = locations.find(city => city.id === value)
    setQuery(selected ? `${selected.name} · ${selected.country}` : value)
  }, [locations, value, editing])

  const matches = editing && query.trim() && locations.length
    ? locations.filter(city => `${city.name} ${city.country} ${city.id} ${(city.aliases ?? []).join(' ')}`.toLowerCase().includes(query.trim().toLowerCase())).slice(0, 20)
    : []
  return <div className="birth-location-picker">
    <label>出生地<input required disabled={loading || locations.length === 0} autoComplete="off" placeholder="搜索出生城市" value={query} onFocus={() => {
      if (value && locations.length && !locations.some(city => city.id === value)) setEditing(true)
    }} onChange={event => {
      setEditing(true)
      setQuery(event.target.value)
      onChange(locations.length ? '' : event.target.value)
    }} /></label>
    {locations.length > 0 && (editing || (value && !locations.some(city => city.id === value))) && <p>请从搜索结果中选择出生地。</p>}
    {matches.length > 0 && <ul aria-label="出生地搜索结果">{matches.map(city => <li key={city.id}>
      <button type="button" onClick={() => { onChange(city.id); setEditing(false) }}>
        {city.name} · {city.country} <small>{city.id}</small>
      </button>
    </li>)}</ul>}
    {locations.length > 0 && editing && query.trim() !== '' && matches.length === 0 && <p>没有找到匹配的城市，请换个名称搜索。</p>}
    {loading ? <p role="status">正在加载城市列表…</p> : locations.length === 0 && <><p>城市列表暂不可用，无法确认出生地，请重试。</p>{onRetry && <button type="button" onClick={onRetry}>重试加载城市</button>}</>}
  </div>
}
