import React from 'react'
import { useProductLanguage, type ProductLanguage } from '../../productLanguage'

interface HeaderProps {
  brand?: string
  timezone?: string
  lang?: string
  onLangChange?: () => void
  onTimezoneChange?: () => void
}

const Header: React.FC<HeaderProps> = ({ brand = 'LIORIN', timezone, lang = '中文' }) => {
  const language = useProductLanguage()
  return (
  <header className="app-header">
    <div className="app-brand">{brand}<span> / 顺天</span></div>
    <div className="app-header-meta" aria-label="当前显示设置">
      {language ? <select aria-label="Product language" value={language.locale}
        onChange={event => language.choose(event.target.value as ProductLanguage)}>
        <option value="en">English</option><option value="zh-Hans">简体中文</option><option value="zh-Hant">繁體中文</option>
      </select> : <span className="app-meta-item"><span aria-hidden="true">◎</span> {lang}</span>}
      {timezone && <span className="app-meta-item"><span aria-hidden="true">◷</span> {timezone}</span>}
    </div>
  </header>
  )
}
export default Header
