import React, { useLayoutEffect, useRef } from 'react'
import Header from './Header'
import './AppShell.css'
import BottomNav, { type PageName } from '../navigation/BottomNav'

interface AppShellProps {
  children: React.ReactNode
  activePage: PageName | null
  onPageChange: (page: PageName) => void
  timezone?: string
  lang?: string
  onLangChange?: () => void
  onTimezoneChange?: () => void
  entitlementLabel?: string
  viewKey?: string | boolean
}

/**
 * App Shell — Section 31 of LIORIN spec
 * Header + Main + BottomNav layout
 */
const AppShell: React.FC<AppShellProps> = ({
  children,
  activePage,
  onPageChange,
  timezone,
  lang = '中文',
  onLangChange,
  onTimezoneChange,
  entitlementLabel,
  viewKey,
}) => {
  const mainRef = useRef<HTMLElement>(null)
  useLayoutEffect(() => {
    if (mainRef.current) mainRef.current.scrollTop = 0
  }, [activePage, viewKey])
  return (
    <div className="app-shell" style={{ display: 'grid', gridTemplateRows: 'auto 1fr auto', height: '100vh', overflow: 'hidden' }}>
      <Header
        timezone={timezone}
        lang={lang}
        onLangChange={onLangChange}
        onTimezoneChange={onTimezoneChange}
      />
      <main
        ref={mainRef}
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
