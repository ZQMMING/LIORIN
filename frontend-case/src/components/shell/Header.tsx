import React from 'react'

interface HeaderProps {
  brand?: string
  timezone?: string
  lang?: string
  onLangChange?: () => void
  onTimezoneChange?: () => void
}

const Header: React.FC<HeaderProps> = ({ brand = 'LIORIN', timezone, lang = '中文' }) => (
  <header className="app-header">
    <div className="app-brand">{brand}<span> / 顺天</span></div>
    <div className="app-header-meta" aria-label="当前显示设置">
      <span className="app-meta-item"><span aria-hidden="true">◎</span> {lang}</span>
      {timezone && <span className="app-meta-item"><span aria-hidden="true">◷</span> {timezone}</span>}
    </div>
  </header>
)
export default Header
