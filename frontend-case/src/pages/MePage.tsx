import React, { useEffect, useState } from 'react'
import './support-pages.css'
import { checkAuthAvailability, type AuthAvailability } from '../api/authAvailability'

const availabilityMessage: Record<AuthAvailability, string> = {
  loading: '正在检查认证服务…',
  available: '认证服务可用；当前仍是游客。登录入口尚未接入。',
  unavailable: '认证服务尚未装配，当前无法建档或登录。',
  offline: '暂时无法连接认证服务，请检查本地后端。',
}

const MePage: React.FC = () => {
  const [authAvailability, setAuthAvailability] = useState<AuthAvailability>('loading')
  useEffect(() => {
    let active = true
    void checkAuthAvailability().then((state) => {
      if (active) setAuthAvailability(state)
    })
    return () => { active = false }
  }, [])
  const menuItems = [
    { label: 'PROFILE', title: '个人档案尚未开放', sub: '尚未开放' },
    { label: 'CHART', title: '个人命盘暂不可用', sub: '尚未开放' },
    { label: 'CLASSICS', title: '经典与来源', sub: '内容整理中' },
    { label: 'SETTINGS', title: '偏好设置', sub: '尚未开放' },
    { label: 'SUBSCRIPTION', title: '订阅与权益', sub: '尚未开放' },
  ]
  return (
    <main className="support-page me-page">
      <header className="support-header">
        <span className="support-eyebrow">ME / 我的</span>
        <h1>你的空间。</h1>
        <p>个人资料与设置将汇集在这里。当前可先探索公共时间信息。</p>
      </header>
      <section className="me-identity" aria-label="当前账户状态">
        <span className="me-identity-symbol" aria-hidden="true">○</span>
        <div><span className="support-eyebrow">PUBLIC</span><h2>游客</h2><p role="status">{availabilityMessage[authAvailability]}</p></div>
      </section>
      <div className="me-list">
        {menuItems.map((item, i) => <div className="me-row" key={item.label}>
          <span className="me-number">0{i + 1}</span>
          <div><span className="me-label">{item.label}</span><h2>{item.title}</h2></div>
          <span className="me-unavailable">{item.sub}</span>
        </div>)}
      </div>
      <footer className="me-footer">LIORIN · 顺天 <span>TIME, IN YOUR OWN RHYTHM</span></footer>
    </main>
  )
}
export default MePage
