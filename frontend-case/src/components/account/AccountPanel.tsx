import { useState } from 'react'
import { ApiClientError } from '../../api/http'
import { fetchMe, loginWithPairing, logout, type AuthTokens } from '../../api/auth'
import { readStoredProfile, saveStoredProfile } from '../../api/profile'
import type { ProfileRequest } from '../../contracts/profile'

interface Props { available: boolean }

type Action = 'login' | 'save' | 'load' | 'logout' | null

function readableError(error: unknown): string {
  if (error instanceof ApiClientError) {
    if (error.status === 503) return '服务尚未装配，请稍后再试。'
    if (error.status === 401) return '身份凭据已失效，请重新登录。'
    if (error.status === 422) return '资料不完整或不符合后端校验，请检查输入。'
  }
  return '操作失败，请稍后重试。'
}

/** 凭据仅保存在组件内存；关闭/刷新页面即清除，不写 localStorage。 */
export default function AccountPanel({ available }: Props) {
  const [tokens, setTokens] = useState<AuthTokens | null>(null)
  const [userId, setUserId] = useState('')
  const [deviceId, setDeviceId] = useState('')
  const [pairingCode, setPairingCode] = useState('')
  const [busy, setBusy] = useState<Action>(null)
  const [message, setMessage] = useState('')
  const [birthDate, setBirthDate] = useState('')
  const [hour, setHour] = useState('')
  const [minute, setMinute] = useState('')
  const [gender, setGender] = useState<'male' | 'female'>('male')
  const [timezone, setTimezone] = useState('')
  const [location, setLocation] = useState('')
  const [currentLocation, setCurrentLocation] = useState('')

  async function act(kind: Action, run: () => Promise<void>) {
    setBusy(kind)
    setMessage('')
    try { await run() }
    catch (error) { setMessage(readableError(error)) }
    finally { setBusy(null) }
  }

  function profileRequest(): ProfileRequest {
    return {
      birth_date: birthDate,
      birth_time: { hour: Number(hour), minute: minute === '' ? null : Number(minute) },
      gender, timezone, location, current_location: currentLocation,
      calendar_system: 'solar',
    }
  }

  return <section className="account-panel" aria-label="账户与档案">
    {!tokens ? <>
      <h2>账户</h2>
      <p>凭据仅保留在本页内存，刷新后需重新配对登录。匿名建号的账户恢复流程未完成，暂不开放注册，避免生成无法找回的账户。</p>
      <form onSubmit={(event) => { event.preventDefault(); void act('login', async () => {
        const result = await loginWithPairing(deviceId, pairingCode)
        const me = await fetchMe(result.access_token)
        setTokens(result)
        setUserId(me.user_id)
        setPairingCode('')
        setMessage('登录成功。')
      }) }}>
        <label>设备 ID<input required value={deviceId} onChange={e => setDeviceId(e.target.value)} /></label>
        <label>配对码<input required type="password" autoComplete="off" value={pairingCode} onChange={e => setPairingCode(e.target.value)} /></label>
        <button type="submit" disabled={!available || busy !== null}>设备配对登录</button>
      </form>
    </> : <>
      <h2>已登录账户</h2><p>用户 ID：{userId}</p>
      <button type="button" disabled={busy !== null} onClick={() => void act('logout', async () => {
        await logout(tokens.access_token, tokens.refresh_token)
        setTokens(null); setUserId(''); setMessage('已退出。')
      })}>退出</button>
      <h2>出生档案</h2>
      <p>只有点击「保存档案」后才会发送出生资料；不保存于浏览器。服务端须已完成独立迁移。</p>
      <form onSubmit={event => { event.preventDefault(); void act('save', async () => {
        const result = await saveStoredProfile(profileRequest(), tokens.access_token)
        if (result.stored !== true) throw new Error('profile not stored')
        setMessage('档案已由后端确认保存。')
      }) }}>
        <label>出生日期<input required type="date" value={birthDate} onChange={e => setBirthDate(e.target.value)} /></label>
        <label>出生小时（0–23）<input required type="number" min="0" max="23" value={hour} onChange={e => setHour(e.target.value)} /></label>
        <label>出生分钟（可选）<input type="number" min="0" max="59" value={minute} onChange={e => setMinute(e.target.value)} /></label>
        <label>性别<select value={gender} onChange={e => setGender(e.target.value as 'male' | 'female')}><option value="male">男</option><option value="female">女</option></select></label>
        <label>时区（IANA）<input required placeholder="Asia/Shanghai" value={timezone} onChange={e => setTimezone(e.target.value)} /></label>
        <label>出生地<input required placeholder="Beijing" value={location} onChange={e => setLocation(e.target.value)} /></label>
        <label>当前城市<input required value={currentLocation} onChange={e => setCurrentLocation(e.target.value)} /></label>
        <button type="submit" disabled={busy !== null}>保存档案</button>
        <button type="button" disabled={busy !== null} onClick={() => void act('load', async () => {
          const saved = await readStoredProfile(tokens.access_token)
          setBirthDate(saved.birth_date)
          setHour(String(saved.birth_time.hour))
          setMinute(saved.birth_time.minute == null ? '' : String(saved.birth_time.minute))
          setGender(saved.gender)
          setTimezone(saved.timezone ?? '')
          setLocation(saved.location ?? '')
          setCurrentLocation(saved.current_location ?? '')
          setMessage('已从后端读取档案；未进行命理计算。')
        })}>读取已存档案</button>
      </form>
    </>}
    {message && <p role="status">{message}</p>}
  </section>
}
