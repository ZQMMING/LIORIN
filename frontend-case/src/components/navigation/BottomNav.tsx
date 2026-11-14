import React from 'react'
import './BottomNav.css'

export type PageName = 'today' | 'guide' | 'insights' | 'me' | 'more'

interface BottomNavProps {
  activePage: PageName | null
  onPageChange: (page: PageName) => void
  entitlementLabel?: string
}

interface TabDef {
  name: PageName
  label: string
  icon: (active: boolean) => React.ReactNode
}

const iconStroke = (active: boolean) => active ? 'var(--gold-light)' : 'currentColor'
const iconFill = (active: boolean) => active ? 'var(--gold-soft)' : 'none'

const TABS: TabDef[] = [
  {
    name: 'today',
    label: '今日',
    icon: (active) => (
      <svg width="20" height="20" viewBox="0 0 24 24" fill={iconFill(active)} stroke={iconStroke(active)} strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
        <circle cx="12" cy="12" r="9" />
        <path d="M12 3a14 14 0 0 1 0 18" />
        <path d="M12 3a14 14 0 0 0 0 18" />
        <line x1="3" y1="12" x2="21" y2="12" />
      </svg>
    ),
  },
  {
    name: 'guide',
    label: '指引',
    icon: (active) => (
      <svg width="20" height="20" viewBox="0 0 24 24" fill={iconFill(active)} stroke={iconStroke(active)} strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
        <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" />
        <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z" />
        <line x1="9" y1="7" x2="15" y2="7" />
        <line x1="9" y1="11" x2="15" y2="11" />
      </svg>
    ),
  },
  {
    name: 'insights',
    label: '洞察',
    icon: (active) => (
      <svg width="20" height="20" viewBox="0 0 24 24" fill={iconFill(active)} stroke={iconStroke(active)} strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
        <path d="M12 2a7 7 0 0 0-4 12.7V17a2 2 0 0 0 2 2h4a2 2 0 0 0 2-2v-2.3A7 7 0 0 0 12 2z" />
        <line x1="9" y1="22" x2="15" y2="22" />
        <line x1="12" y1="6" x2="12" y2="12" />
      </svg>
    ),
  },
  {
    name: 'me',
    label: '我的',
    icon: (active) => (
      <svg width="20" height="20" viewBox="0 0 24 24" fill={iconFill(active)} stroke={iconStroke(active)} strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
        <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
        <circle cx="12" cy="7" r="4" />
      </svg>
    ),
  },
  {
    name: 'more',
    label: '更多',
    icon: (active) => (
      <svg width="20" height="20" viewBox="0 0 24 24" fill={iconFill(active)} stroke={iconStroke(active)} strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
        <rect x="3" y="3" width="7" height="7" rx="1" />
        <rect x="14" y="3" width="7" height="7" rx="1" />
        <rect x="3" y="14" width="7" height="7" rx="1" />
        <rect x="14" y="14" width="7" height="7" rx="1" />
      </svg>
    ),
  },
]

const BottomNav: React.FC<BottomNavProps> = ({ activePage, onPageChange, entitlementLabel }) => {
  return (
    <nav className="bottom-nav-v2" role="navigation" aria-label="主导航">
      <div className="bottom-nav-bg" aria-hidden="true" />
      <div className="bottom-nav-inner">
        {TABS.map((tab) => {
          const isActive = activePage === tab.name
          const label = tab.name === 'more' ? (entitlementLabel || tab.label) : tab.label
          return (
            <button
              key={tab.name}
              className={`nav-item-v2${isActive ? ' active' : ''}`}
              onClick={() => onPageChange(tab.name)}
              aria-current={isActive ? 'page' : undefined}
              aria-label={label}
            >
              <span className="nav-indicator" aria-hidden="true" />
              <span className="nav-icon-wrap">
                {tab.icon(isActive)}
              </span>
              <span className="nav-label">{label}</span>
            </button>
          )
        })}
      </div>
      <div className="bottom-nav-safe-area" aria-hidden="true" />
    </nav>
  )
}

export default BottomNav
