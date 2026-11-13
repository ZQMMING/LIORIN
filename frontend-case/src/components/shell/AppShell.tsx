import React from 'react'
import Header from './Header'
import './AppShell.css'
import BottomNav, { type PageName } from '../navigation/BottomNav'

interface AppShellProps {
  children: React.ReactNode
  activePage: PageName
  onPageChange: (page: PageName) => void
  timezone?: string
  lang?: string
  onLangChange?: () => void
  onTimezoneChange?: () => void
  entitlementLabel?: string
}

/**
 * App Shell — Section 31 of LIORIN spec
 * Header + Main + BottomNav layout
 */
const AppShell: React.FC<AppShellProps> = ({
  children,
  activePage,
  onPageChange,
  timezone = 'GMT+8',
  lang = '中文',
  onLangChange,
  onTimezoneChange,
  entitlementLabel,
}) => {
  return (
    <div className="app-shell" style={{ display: 'grid', gridTemplateRows: 'auto 1fr auto', height: '100vh', overflow: 'hidden' }}>
      <Header
        timezone={timezone}
        lang={lang}
        onLangChange={onLangChange}
        onTimezoneChange={onTimezoneChange}
      />
      <main
        className="app-main"
        style={{
          overflowY: 'auto',
          scrollBehavior: 'smooth',
        }}
        role="main"
      >
        {children}
      </main>
      <BottomNav
        activePage={activePage}
        onPageChange={onPageChange}
        entitlementLabel={entitlementLabel}
      />
    </div>
  )
}

export default AppShell
