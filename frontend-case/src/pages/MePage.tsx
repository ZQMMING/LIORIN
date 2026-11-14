import React, { useEffect, useState } from 'react'
import EngineQaPage from './EngineQaPage'
import './support-pages.css'
import { checkAuthAvailability, type AuthAvailability } from '../api/authAvailability'
import AccountPanel from '../components/account/AccountPanel'
import type { AuthTokens } from '../api/auth'

const availabilityMessage: Record<AuthAvailability, string> = {
  loading: '正在检查认证服务…',
  available: '认证服务可用；可尝试使用下方邮箱登录。',
  unavailable: '认证服务尚未装配，当前无法建档或登录。',
  offline: '暂时无法连接认证服务，请检查本地后端。',
}

const MePage: React.FC<{
  session?: AuthTokens | null
  onSessionChange?: (tokens: AuthTokens | null) => void
  onProfileReady?: () => void
}> = ({ session, onSessionChange, onProfileReady }) => {
  const [authAvailability, setAuthAvailability] = useState<AuthAvailability>('loading')
  const [showQa, setShowQa] = useState(false)
  useEffect(() => {
    let active = true
    void checkAuthAvailability().then((state) => {
      if (active) setAuthAvailability(state)
    })
    return () => { active = false }
  }, [])
  if (showQa && import.meta.env.VITE_LIORIN_LOCAL_PREVIEW === '1') {
    return <><button type="button" onClick={() => setShowQa(false)}>返回我的</button><EngineQaPage /></>
  }
  const menuItems = [
    { label: 'PROFILE', title: '档案管理', sub: '见上方账户区域' },
    { label: 'CHART', title: '个人命盘暂不可用', sub: '尚未开放' },
    { label: 'CLASSICS', title: '经典与来源', sub: '内容整理中' },
    { label: 'SETTINGS', title: '偏好设置', sub: '尚未开放' },
    { label: 'SUBSCRIPTION', title: '订阅与权益', sub: '尚未开放' },
  ]
  return (
    <div className="support-page me-page">
      <header className="support-header">
        <span className="support-eyebrow">ME / 我的</span>
        <h1>你的空间。</h1>
        <p>个人资料与设置将汇集在这里。当前可先探索公共时间信息。</p>
      </header>
      <section className="me-identity" aria-label="当前账户状态">
        <span className="me-identity-symbol" aria-hidden="true">○</span>
        <div><span className="support-eyebrow">{session ? 'PERSONAL' : 'PUBLIC'}</span><h2>{session ? '已登录' : '游客'}</h2><p role="status">{session ? '当前会话仅保存在本页内存。' : availabilityMessage[authAvailability]}</p></div>
      </section>
      {import.meta.env.VITE_LIORIN_LOCAL_PREVIEW === '1' &&
        <button type="button" onClick={() => setShowQa(true)}>打开引擎测试工作台（TEST ONLY）</button>}
      <AccountPanel available={authAvailability === 'available'} session={session} onSessionChange={onSessionChange} onProfileReady={onProfileReady} />
      <div className="me-list">
        {menuItems.map((item, i) => <div className="me-row" key={item.label}>
          <span className="me-number">0{i + 1}</span>
          <div><span className="me-label">{item.label}</span><h2>{item.title}</h2></div>
          <span className="me-unavailable">{item.sub}</span>
        </div>)}
      </div>
      <footer className="me-footer">LIORIN · 顺天 <span>TIME, IN YOUR OWN RHYTHM</span></footer>
    </div>
  )
}
export default MePage
