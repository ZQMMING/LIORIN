import { useEffect, useState } from 'react'
import { ApiClientError } from '../../api/http'
import { fetchMe, loginWithPairing, logout, requestEmailCode, verifyEmailCode, type AuthTokens } from '../../api/auth'
import { readStoredProfile, saveStoredProfile } from '../../api/profile'
import type { ProfileRequest } from '../../contracts/profile'
import './account-panel.css'
import { fetchBirthLocations, type BirthLocation } from '../../api/locations'
import BirthLocationPicker from './BirthLocationPicker'

interface Props {
  available: boolean
  session?: AuthTokens | null
  onSessionChange?: (tokens: AuthTokens | null) => void
  onProfileReady?: () => void
}

type Action = 'request-code' | 'verify-code' | 'login' | 'save' | 'load' | 'logout' | null

function readableError(error: unknown): string {
  if (error instanceof ApiClientError) {
    if (error.normalized.code === 'PROFILE_NOT_FOUND') return '当前账户还没有保存出生档案，请填写后保存。'
    if (error.normalized.code === 'PROFILE_LOCATION_AMBIGUOUS') return '出生地有多个匹配，请重新搜索并选择具体城市。'
    if (error.normalized.code === 'PROFILE_STORE_UNAVAILABLE') return '档案服务暂不可用，本次操作未完成，请稍后重试。'
    if (error.normalized.code === 'EMAIL_AUTH_UNAVAILABLE') return '邮箱登录服务暂不可用，请稍后重试。'
    if (error.normalized.code === 'EMAIL_COOLDOWN') return '请求过于频繁，请稍等后再获取验证码。'
    if (error.status === 503) return '服务尚未装配，请稍后再试。'
    if (error.status === 401) return '身份凭据已失效，请重新登录。'
    const fields = new Set((error.normalized.details ?? []).flatMap(item => [item.field, ...(item.loc ?? [])]))
    if (fields.has('location')) return '出生地无法识别，请检查城市名称后重试。'
    if (fields.has('timezone')) return '时区无法识别，请填写有效的时区名称，例如 Asia/Shanghai。'
    if (fields.has('gender')) return '请选择性别后重试。'
    if (fields.has('birth_date')) return '出生日期不正确，请检查后重试。'
    if (fields.has('birth_time') || fields.has('hour') || fields.has('minute')) return '出生时间不正确，请检查小时和分钟。'
    if (error.status === 400) return '资料未通过校验，请检查出生地、时区及出生日期。'
    if (error.status === 422) return '资料不完整或不符合后端校验，请检查输入。'
  }
  return '操作失败，请稍后重试。'
}

/** Access tokens remain in memory; email sessions restore via an HttpOnly cookie. */
export default function AccountPanel({ available, session, onSessionChange, onProfileReady }: Props) {
  const [tokens, setTokens] = useState<AuthTokens | null>(session ?? null)
  const [userId, setUserId] = useState(session?.user_id ?? '')
  const [profileSaved, setProfileSaved] = useState(false)
  useEffect(() => {
    if (session !== undefined) {
      setTokens(session)
      setUserId(session?.user_id ?? '')
      if (!session) {
        setProfileSaved(false)
        setBirthDate(''); setHour(''); setMinute(''); setGender('')
        setTimezone(''); setLocation(''); setCurrentLocation('')
      }
    }
  }, [session])
  const [email, setEmail] = useState('')
  const [emailCode, setEmailCode] = useState('')
  const [deviceId, setDeviceId] = useState('')
  const [pairingCode, setPairingCode] = useState('')
  const [busy, setBusy] = useState<Action>(null)
  const [message, setMessage] = useState('')
  const [birthDate, setBirthDate] = useState('')
  const [hour, setHour] = useState('')
  const [minute, setMinute] = useState('')
  const [gender, setGender] = useState<'male' | 'female' | ''>('')
  const [timezone, setTimezone] = useState('')
  const [location, setLocation] = useState('')
  const [locationReset, setLocationReset] = useState(0)
  const [currentLocation, setCurrentLocation] = useState('')
  const [birthLocations, setBirthLocations] = useState<BirthLocation[]>([])
  const [locationsPending, setLocationsPending] = useState(true)
  const [locationsAttempt, setLocationsAttempt] = useState(0)
  useEffect(() => {
    let active = true
    if (tokens) {
      setLocationsPending(true)
      void fetchBirthLocations().then(locations => { if (active) setBirthLocations(locations) }).catch(() => { if (active) setBirthLocations([]) }).finally(() => { if (active) setLocationsPending(false) })
    }
    return () => { active = false }
  }, [tokens, locationsAttempt])

  async function act(kind: Action, run: () => Promise<void>) {
    setBusy(kind)
    setMessage('')
    try { await run() }
    catch (error) {
      if (error instanceof ApiClientError && error.status === 401 && (kind === 'save' || kind === 'load' || kind === 'logout')) {
        setTokens(null); setUserId(''); setProfileSaved(false)
        setBirthDate(''); setHour(''); setMinute(''); setGender('')
        setTimezone(''); setLocation(''); setCurrentLocation('')
        onSessionChange?.(null)
      }
      setMessage(error instanceof ApiClientError && error.status === 401 && kind === 'verify-code'
        ? '验证码不正确或已过期，请检查后重试。'
        : readableError(error))
    }
    finally { setBusy(null) }
  }

  function profileRequest(): ProfileRequest {
    if (!gender) throw new Error('gender not selected')
    return {
      birth_date: birthDate,
      birth_time: { hour: Number(hour), minute: minute === '' ? null : Number(minute) },
      gender, timezone: timezone.trim() || null, location, current_location: currentLocation.trim() || null,
      calendar_system: 'solar',
    }
  }

  return <section className="account-panel" aria-label="账户与档案">
    {!tokens ? <>
      <h2>账户</h2>
      <p>使用邮箱验证码登录或注册同一账户。刷新后可恢复有效会话；退出后需重新登录。</p>
      <form onSubmit={(event) => { event.preventDefault(); void act('request-code', async () => {
        await requestEmailCode(email)
        setMessage('如果邮箱可接收邮件，验证码已发送。请在 10 分钟内输入。')
      }) }}>
        <label>邮箱<input required disabled={busy !== null} type="email" autoComplete="email" value={email} onChange={e => setEmail(e.target.value)} /></label>
        <button type="submit" disabled={!available || busy !== null}>发送验证码</button>
      </form>
      <form onSubmit={(event) => { event.preventDefault(); void act('verify-code', async () => {
        const result = await verifyEmailCode(email, emailCode)
        const me = await fetchMe(result.access_token)
        if (me.user_id !== result.user_id) throw new Error('authentication identity mismatch')
        setTokens(result)
        onSessionChange?.(result)
        setUserId(me.user_id)
        setEmailCode('')
        setMessage('邮箱验证成功，已登录同一账户。')
      }) }}>
        <label>邮箱验证码<input required disabled={busy !== null} inputMode="numeric" pattern="[0-9]{6}" maxLength={6} autoComplete="one-time-code" value={emailCode} onChange={e => setEmailCode(e.target.value)} /></label>
        <button type="submit" disabled={!available || busy !== null || !email}>验证并登录</button>
      </form>
      <form onSubmit={(event) => { event.preventDefault(); void act('login', async () => {
        const result = await loginWithPairing(deviceId, pairingCode)
        const me = await fetchMe(result.access_token)
        if (me.user_id !== result.user_id) throw new Error('authentication identity mismatch')
        setTokens(result)
        onSessionChange?.(result)
        setUserId(me.user_id)
        setPairingCode('')
        setMessage('登录成功。')
      }) }}>
        <label>设备 ID<input required disabled={busy !== null} value={deviceId} onChange={e => setDeviceId(e.target.value)} /></label>
        <label>配对码<input required disabled={busy !== null} type="password" autoComplete="off" value={pairingCode} onChange={e => setPairingCode(e.target.value)} /></label>
        <button type="submit" disabled={!available || busy !== null}>设备配对登录</button>
      </form>
    </> : <>
      <h2>已登录账户</h2><p>用户 ID：{userId}</p>
      <button type="button" disabled={busy !== null} onClick={() => void act('logout', async () => {
        setTokens(null); onSessionChange?.(null); setUserId(''); setProfileSaved(false)
        setBirthDate(''); setHour(''); setMinute(''); setGender('')
        setTimezone(''); setLocation(''); setCurrentLocation('')
        try {
          await logout(tokens.access_token, tokens.refresh_token)
          setMessage('已退出。')
        } catch {
          setMessage('本页面已退出；服务器未确认撤销原会话。')
        }
      })}>退出</button>
      <h2>出生档案</h2>
      <p>请填写出生信息。已有档案可先点击“读取已存档案”；保存时资料会发送至账户服务。</p>
      <form onChange={() => setProfileSaved(false)} onSubmit={event => { event.preventDefault(); void act('save', async () => {
        const result = await saveStoredProfile(profileRequest(), tokens.access_token)
        if (result.stored !== true) throw new Error('profile not stored')
        setProfileSaved(true)
        setMessage('档案已由后端确认保存。')
      }) }}>
        <fieldset disabled={busy !== null}>
        <label>出生日期<input required type="date" value={birthDate} onChange={e => setBirthDate(e.target.value)} /></label>
        <label>出生时间<input required type="time" value={hour !== '' && minute !== '' ? `${hour.padStart(2, '0')}:${minute.padStart(2, '0')}` : ''} onChange={e => {
          const [h, m] = e.target.value ? e.target.value.split(':') : ['', '']
          setHour(h); setMinute(m)
        }} /></label>
        <p>请填写准确出生时间；不确定时暂不要提交，系统不会替你猜测。</p>
        <label>性别<select required value={gender} onChange={e => setGender(e.target.value as 'male' | 'female' | '')}><option value="">请选择</option><option value="male">男</option><option value="female">女</option></select></label>
        <label>时区（可选）<input placeholder="例如 Asia/Shanghai" value={timezone} onChange={e => setTimezone(e.target.value)} /></label>
        <BirthLocationPicker key={locationReset} loading={locationsPending} onRetry={() => setLocationsAttempt(n => n + 1)} locations={birthLocations} value={location} onChange={value => { setLocation(value); setProfileSaved(false) }} />
        <p>出生地用于时间换算。时区留空时由服务端根据出生地识别；如需指定，请填写 IANA 时区名称。</p>
        <label>当前城市（可选）<input value={currentLocation} onChange={e => setCurrentLocation(e.target.value)} /></label>
        <button type="submit" disabled={busy !== null || locationsPending || !location || !birthLocations.some(city => city.id === location)}>保存档案</button>
        <button type="button" disabled={busy !== null} onClick={() => void act('load', async () => {
          const saved = await readStoredProfile(tokens.access_token)
          setBirthDate(saved.birth_date)
          setHour(String(saved.birth_time.hour))
          setMinute(saved.birth_time.minute == null ? '' : String(saved.birth_time.minute))
          setGender(saved.gender)
          setTimezone(saved.timezone ?? '')
          setLocation(saved.location ?? '')
          setLocationReset(n => n + 1)
          setCurrentLocation(saved.current_location ?? '')
          setProfileSaved(true)
          setMessage('已从后端读取档案；未进行命理计算。')
        })}>读取已存档案</button>
        </fieldset>
      </form>
      {profileSaved && onProfileReady && <button type="button" onClick={onProfileReady}>查看个人今日</button>}
    </>}
    {message && <p role="status">{message}</p>}
  </section>
}
