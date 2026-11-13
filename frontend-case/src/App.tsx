import { useState, useCallback, useEffect } from 'react'
import './paper-theme.css'
import AppShell from './components/shell/AppShell'
import PersonalToday from './pages/today/PersonalToday'
import RealPublicToday from './pages/today/RealPublicToday'
import GuidePage from './pages/GuidePage'
import InsightsPage from './pages/InsightsPage'
import MePage from './pages/MePage'
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
  const [currentPage, setCurrentPage] = useState<PageName>('today')
  const [simState, setSimState] = useState<SimulatedState>('public')
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
    if (effectiveState === 'public') {
      void loadRealToday()
    }
  }, [effectiveState, loadRealToday])

  const entitlement = getEntitlement(effectiveState)
  const data = getTodayData(effectiveState)
  const isMockState = effectiveState !== 'public'

  const handleLangChange = useCallback(() => {}, [])
  const handleTimezoneChange = useCallback(() => {}, [])

  const entitlementLabel = entitlement === 'PREMIUM' ? 'Private' : 'More'

  const renderPage = () => {
    switch (currentPage) {
      case 'today':
        if (effectiveState === 'public') {
          // Step B：游客态走真数据 GET /v1/today（FAIL FAST，无 mock 兜底）
          return (
            <RealPublicToday
              view={realToday ? buildRealPublicTodayView(realToday) : null}
              isLoading={realLoading}
              isError={realError}
              onRetry={() => void loadRealToday()}
            />
          )
        }
        return (
          <PersonalToday
            data={data}
            isPremium={entitlement === 'PREMIUM'}
          />
        )
      case 'guide':
        return <GuidePage />
      case 'insights':
        return <InsightsPage />
      case 'me':
        return <MePage />
      default:
        return <section className="page-container" role="status"><h1>功能暂未开放</h1><p>该页面尚无可用的真实数据接口。</p></section>
    }
  }

  return (
    <AppShell
      activePage={currentPage}
      onPageChange={setCurrentPage}
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
      {import.meta.env.DEV && <div
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
