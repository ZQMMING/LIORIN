import { useState, useCallback, useEffect, useRef } from 'react'
import './paper-theme.css'
import AppShell from './components/shell/AppShell'
import PersonalToday from './pages/today/PersonalToday'
import RealPublicToday from './pages/today/RealPublicToday'
import LocalPreviewUnavailable from './pages/today/LocalPreviewUnavailable'
import RealPersonalHeluoToday from './pages/today/RealPersonalHeluoToday'
import HeluoPreviewToday from './pages/today/HeluoPreviewToday'
import EngineQaPage from './pages/EngineQaPage'
import { restoreBrowserSession, type AuthTokens } from './api/auth'
import GuidePage from './pages/GuidePage'
import InsightsPage from './pages/InsightsPage'
import MePage from './pages/MePage'
import MorePage from './pages/MorePage'
import { fetchToday } from './api/today'
import { buildRealPublicTodayView } from './view-models/publicToday'
import type { TodayResponse } from './contracts/today'
import {
  MOCK_PERSONAL_DAY3,
  MOCK_PROFILE_INSUFFICIENT,
  MOCK_PREMIUM,
  MOCK_CALCULATION_ERROR,
} from './mock/data'
import type { PageName } from './components/navigation/BottomNav'
import { pageForPath, pathForPage } from './navigation'
import type { Entitlement, ProfileStatus, TodayData } from './mock/data'

type SimulatedState =
  | 'public'
  | 'authenticated-no-profile'
  | 'authenticated-insufficient'
  | 'authenticated-valid'
  | 'premium'
  | 'calculation-error'

function getTodayData(state: SimulatedState): TodayData {
  switch (state) {
    case 'authenticated-no-profile':
      return { ...MOCK_PROFILE_INSUFFICIENT, user_state: { entitlement: 'AUTHENTICATED', profile_status: 'NONE' as ProfileStatus } }
    case 'authenticated-insufficient':
      return MOCK_PROFILE_INSUFFICIENT
    case 'premium':
      return MOCK_PREMIUM
    case 'calculation-error':
      return MOCK_CALCULATION_ERROR
    default:
      return MOCK_PERSONAL_DAY3
  }
}

function getEntitlement(state: SimulatedState): Entitlement {
  switch (state) {
    case 'public': return 'PUBLIC'
    case 'premium': return 'PREMIUM'
    default: return 'AUTHENTICATED'
  }
}

function App() {
  const productBPreview = import.meta.env.VITE_LIORIN_PRODUCT_B_PREVIEW === '1'
  const [currentPage, setCurrentPage] = useState(() => pageForPath(window.location.pathname))
  const navigate = useCallback((page: PageName) => {
    const path = pathForPage(page)
    if (window.location.pathname !== path) window.history.pushState(null, '', path)
    setCurrentPage(page)
  }, [])
  useEffect(() => {
    const onPopState = () => setCurrentPage(pageForPath(window.location.pathname))
    window.addEventListener('popstate', onPopState)
    return () => window.removeEventListener('popstate', onPopState)
  }, [])
  const [simState, setSimState] = useState<SimulatedState>('public')
  const [session, setSession] = useState<AuthTokens | null>(null)
  const sessionEpoch = useRef(0)
  useEffect(() => {
    let active = true
    const epoch = sessionEpoch.current
    void restoreBrowserSession().then(restored => {
      if (active && sessionEpoch.current === epoch) setSession(restored)
    }).catch(() => { /* no valid cookie: remain signed out */ })
    return () => { active = false }
  }, [])
  const [personalSessionExpired, setPersonalSessionExpired] = useState(false)
  const [showLocalTest, setShowLocalTest] = useState(false)
  const expirePersonalSession = useCallback(() => {
    sessionEpoch.current += 1
    setSession(null)
    setPersonalSessionExpired(true)
  }, [])
  // 模拟个人态只供开发预览；生产没有身份/个人端点闭环时保持游客态。
  const effectiveState: SimulatedState = import.meta.env.DEV ? simState : 'public'

  // ── Step B: Public 层真数据闭环（GET /v1/today）──────────────────
  const [realToday, setRealToday] = useState<TodayResponse | null>(null)
  const [realLoading, setRealLoading] = useState(false)
  const [realError, setRealError] = useState(false)

  const loadRealToday = useCallback(async () => {
    setRealToday(null)
    setRealLoading(true)
    setRealError(false)
    try {
      const resp = await fetchToday()
      // 在异步边界校验契约，避免畸形的 200 响应进入 React 渲染阶段。
      buildRealPublicTodayView(resp)
      setRealToday(resp)
    } catch {
      // FAIL FAST：不回退 mock，错误态交给 ErrorState
      setRealError(true)
    } finally {
      setRealLoading(false)
    }
  }, [])

  useEffect(() => {
    if (!productBPreview && effectiveState === 'public') {
      void loadRealToday()
    }
  }, [effectiveState, loadRealToday, productBPreview])

  const entitlement = getEntitlement(effectiveState)
  const data = getTodayData(effectiveState)
  const isMockState = effectiveState !== 'public'

  const handleLangChange = useCallback(() => {}, [])
  const handleTimezoneChange = useCallback(() => {}, [])

  const entitlementLabel = entitlement === 'PREMIUM' ? '权益' : '更多'

  const renderPage = () => {
    switch (currentPage) {
      case 'today':
        if (productBPreview) return session
          ? <HeluoPreviewToday key={session.user_id} token={session.access_token} onAccount={() => navigate('me')} />
          : <section className="page-container"><h1>Personal Today</h1><p>Sign in to use your saved birth profile.</p><button onClick={() => navigate('me')}>Open account</button></section>
        if (import.meta.env.DEV && import.meta.env.VITE_LIORIN_LOCAL_PREVIEW === '1' && showLocalTest) {
          return <><button className="local-test-back" type="button" onClick={() => setShowLocalTest(false)}>← 返回今日</button><EngineQaPage /></>
        }
        if (personalSessionExpired) return <section className="page-container" role="alert"><h1>个人会话已过期</h1><p>请前往「我的」重新通过邮箱验证码登录；个人结果不会回退为公共数据。</p></section>
        if (session) return <RealPersonalHeluoToday token={session.access_token} onSessionExpired={expirePersonalSession} onProfileRequired={() => navigate('me')} />
        if (effectiveState === 'public') {
          // 本机预览不伪造数据；后端未连接时展示可导航的空状态。
          if (import.meta.env.VITE_LIORIN_LOCAL_PREVIEW === '1' && realError) {
            return <><LocalPreviewUnavailable onRetry={() => void loadRealToday()} />{import.meta.env.DEV && <button className="local-test-entry" type="button" onClick={() => setShowLocalTest(true)}>输入资料 · 本机测试</button>}</>
          }
          // Step B：游客态走真数据 GET /v1/today（FAIL FAST，无 mock 兜底）
          return (
            <><RealPublicToday
              view={realToday ? buildRealPublicTodayView(realToday) : null}
              isLoading={realLoading}
              isError={realError}
              onRetry={() => void loadRealToday()}
            />{import.meta.env.DEV && import.meta.env.VITE_LIORIN_LOCAL_PREVIEW === '1' && !realLoading && <button className="local-test-entry" type="button" onClick={() => setShowLocalTest(true)}>输入资料 · 本机测试</button>}</>
          )
        }
        return (
          <PersonalToday
            data={data}
            isPremium={entitlement === 'PREMIUM'}
            onProfileNext={() => navigate('me')}
          />
        )
      case 'guide':
        return <GuidePage />
      case 'insights':
        return <InsightsPage />
      case 'me':
        return <MePage session={personalSessionExpired ? null : session} onSessionChange={(next) => { sessionEpoch.current += 1; setSession(next); setPersonalSessionExpired(false) }} onProfileReady={() => navigate('today')} />
      case 'more':
        return <MorePage onNavigate={navigate} />
      default:
        return <section className="page-container" role="status"><h1>页面不存在</h1><p>请通过下方导航选择页面。</p><button type="button" onClick={() => navigate('today')}>返回今日</button></section>
    }
  }

  return (
    <AppShell
      activePage={currentPage === 'not-found' ? null : currentPage}
      viewKey={showLocalTest}
      onPageChange={navigate}
      onLangChange={handleLangChange}
      onTimezoneChange={handleTimezoneChange}
      entitlementLabel={entitlementLabel}
    >
      {renderPage()}

      {/* MOCK ONLY 徽标：mock_until 数据未接真，显式标注不冒充真数据（SPEC V2 §红线） */}
      {isMockState && currentPage === 'today' && (
        <div
          aria-label="mock data indicator"
          style={{
            position: 'fixed',
            top: '12px',
            left: '50%',
            transform: 'translateX(-50%)',
            zIndex: 60,
            background: 'var(--bg-elevated)',
            border: '1px dashed var(--border-strong)',
            color: 'var(--text-muted)',
            fontFamily: 'var(--font-mono)',
            fontSize: '9px',
            letterSpacing: '0.1em',
            padding: '4px 10px',
            borderRadius: '2px',
          }}
        >
          MOCK ONLY · 示例数据
        </div>
      )}

      {/* 模拟状态仅供开发预览，不进入生产构建。 */}
      {import.meta.env.DEV && import.meta.env.VITE_LIORIN_LOCAL_PREVIEW !== '1' && <div
        style={{
          position: 'fixed',
          bottom: '68px',
          right: '16px',
          zIndex: 50,
          display: 'flex',
          flexDirection: 'column',
          gap: '4px',
        }}
        aria-label="Dev state switcher"
      >
        {(
          [
            ['public', 'Public'],
            ['authenticated-no-profile', 'No Profile'],
            ['authenticated-insufficient', 'Incomplete'],
            ['authenticated-valid', 'Valid'],
            ['premium', 'Premium'],
            ['calculation-error', 'Error'],
          ] as [SimulatedState, string][]
        ).map(([state, label]) => (
          <button
            key={state}
            onClick={() => setSimState(state)}
            style={{
              background: simState === state ? 'var(--accent)' : 'var(--bg-elevated)',
              border: '1px solid var(--border)',
              color: simState === state ? '#fff' : 'var(--text-muted)',
              fontFamily: 'var(--font-mono)',
              fontSize: '9px',
              letterSpacing: '0.05em',
              cursor: 'pointer',
              padding: '4px 8px',
              transition: 'all 150ms ease',
            }}
          >
            {label}
          </button>
        ))}
      </div>}
    </AppShell>
  )
}

export default App
