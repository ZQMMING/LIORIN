import React, { useState, useEffect, useRef } from 'react'
import FlowHexagram from '../../components/hexagram/FlowHexagram'
import HetuLuoshuHero from '../../components/hexagram/HetuLuoshuHero'
import SixDayCycle from '../../components/hexagram/SixDayCycle'
import TodayYao from '../../components/yao/TodaysYao'
import HeluoCard from '../../components/cards/HeluoCard'
import YijingCard from '../../components/cards/YijingCard'
import ZiweiCard from '../../components/cards/ZiweiCard'
import PremiumGate from '../../components/premium/PremiumGate'
import ProfileGate from '../../components/feedback/ProfileGate'
import ErrorState from '../../components/feedback/ErrorState'
import LoadingState from '../../components/feedback/LoadingState'
import type { TodayData } from '../../mock/data'
import { playHeroAnimation, HeroStage, STAGE_LABELS, type HeroStageValue, BREATHING_CSS } from '../../animation/hero'

interface PersonalTodayProps {
  data: TodayData
  isLoading?: boolean
  onProfileNext?: () => void
  onRetry?: () => void
  isPremium?: boolean
}

/**
 * Personal TODAY page — Sections 3, 6, 7, 13, 14, 15, 16
 */
const PersonalToday: React.FC<PersonalTodayProps> = ({
  data,
  isLoading = false,
  onProfileNext,
  onRetry,
  isPremium = false,
}) => {
  const [heroStage, setHeroStage] = useState<HeroStageValue>(0 as HeroStageValue)
  const [hexagramExpanded, setHexagramExpanded] = useState(false)
  const [cycleCollapsed, setCycleCollapsed] = useState(true)
  const prefersReducedMotion = useRef(
    window.matchMedia('(prefers-reduced-motion: reduce)').matches
  )

  // Run hero animation on mount
  useEffect(() => {
    if (isLoading || !data.hexagram) return
    playHeroAnimation(setHeroStage, prefersReducedMotion.current)
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  if (isLoading) {
    return <LoadingState />
  }

  if (data.user_state.profile_status === 'CALCULATION_ERROR') {
    return <ErrorState type="calculation" onRetry={onRetry} />
  }

  if (data.user_state.profile_status === 'NONE') {
    return <ProfileGate status="NONE" onNext={onProfileNext} />
  }

  if (data.user_state.profile_status === 'INSUFFICIENT') {
    return <ProfileGate status="INSUFFICIENT" onNext={onProfileNext} />
  }

  if (!data.hexagram || !data.active_yao || !data.cycle) {
    return <ErrorState type="network" onRetry={onRetry} />
  }

  const { hexagram, active_yao, cycle, yao_text, guidance, evidence, date_label } = data
  const { position, type } = active_yao
  const yaoNames = ['初爻', '二爻', '三爻', '四爻', '五爻', '上爻']

  return (
    <>
      <style>{BREATHING_CSS}</style>

      {/* Hero */}
      <section
        className="personal-hero"
        aria-label="Personal flow hexagram"
        style={{
          minHeight: '100vh',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          padding: '48px 24px',
          position: 'relative',
        }}
      >
        {/* Stage label */}
        <div
          style={{
            position: 'absolute',
            top: '24px',
            fontSize: '9px',
            letterSpacing: '0.2em',
            textTransform: 'uppercase',
            color: heroStage === 0 ? 'var(--text-muted)' : 'var(--text-secondary)',
            transition: 'color 300ms ease',
          }}
        >
          {heroStage > 0 ? STAGE_LABELS[heroStage as HeroStageValue] || '今日之象' : ''}
        </div>

        {/* Hero: 河洛 animation during stages 0-7, hexagram reveal at stage 8 */}
        {heroStage < HeroStage.TODAY_REVEAL ? (
          <HetuLuoshuHero stage={heroStage} prefersReducedMotion={prefersReducedMotion.current} />
        ) : (
          <FlowHexagram
            hexagram={hexagram}
            activeYao={active_yao}
            cycleDay={cycle.cycle_day}
            totalDays={cycle.total_days}
            onExpand={() => setHexagramExpanded((v) => !v)}
            expanded={hexagramExpanded}
          />
        )}

        {/* Date label */}
        <div
          style={{
            fontFamily: 'var(--font-mono)',
            fontSize: '11px',
            letterSpacing: '0.1em',
            color: 'var(--text-muted)',
            marginTop: '24px',
            textAlign: 'center',
          }}
        >
          {date_label}
        </div>
      </section>

      {/* Content */}
      <section
        className="personal-content"
        style={{
          maxWidth: '640px',
          margin: '0 auto',
          padding: '0 24px 48px',
        }}
      >
        {/* Six-day cycle (expandable) */}
        {hexagramExpanded && (
          <SixDayCycle
            hexagram={hexagram}
            activeYao={active_yao}
            cycleDay={cycle.cycle_day}
            totalDays={cycle.total_days}
            collapsed={cycleCollapsed}
            onToggle={() => setCycleCollapsed((v) => !v)}
          />
        )}

        <div style={{ width: '100%', height: '1px', background: 'var(--border)', margin: '24px 0' }} />

        {/* Today's Yao */}
        <TodayYao
          position={position}
          type={type}
          classicalText={yao_text.classical}
          modernText={yao_text.modern}
          actions={guidance.actions}
        />

        <div style={{ width: '100%', height: '1px', background: 'var(--border)', margin: '24px 0' }} />

        {/* State summary */}
        <div style={{ marginBottom: '24px' }}>
          <div style={{
            fontSize: '9px', letterSpacing: '0.2em', textTransform: 'uppercase',
            color: 'var(--text-muted)', marginBottom: '8px',
          }}>
            State
          </div>
          <h2 style={{
            fontFamily: 'var(--font-display)', fontSize: '18px', fontWeight: 400,
            color: 'var(--text-primary)', marginBottom: '8px', lineHeight: 1.4,
          }}>
            {guidance.opportunity}
          </h2>
          <p style={{ fontSize: '13px', color: 'var(--text-secondary)', lineHeight: 1.7 }}>
            {yao_text.modern}
          </p>
        </div>

        {/* Three domains: Heluo / Yijing / Ziwei */}
        <div style={{ display: 'flex', flexDirection: 'column' }}>
          <HeluoCard
            premiumOnly
            isPremium={isPremium}
          />
          <YijingCard
            hexagramName={hexagram.name}
            yaoName={yaoNames[position - 1]}
            premiumOnly
            isPremium={isPremium}
          />
          <ZiweiCard premiumOnly isPremium={isPremium} />
        </div>

        {/* Premium gate */}
        {!isPremium && (
          <PremiumGate />
        )}

        {/* Evidence */}
        <div style={{ marginTop: '24px', paddingTop: '16px', borderTop: '1px solid var(--border)' }}>
          <div style={{
            fontSize: '9px', letterSpacing: '0.2em', textTransform: 'uppercase',
            color: 'var(--text-muted)', marginBottom: '8px',
          }}>
            Evidence
          </div>
          <p style={{
            fontSize: '12px', color: 'var(--text-muted)', lineHeight: 1.7,
            fontFamily: 'var(--font-display)',
          }}>
            {evidence}
          </p>
        </div>
      </section>
    </>
  )
}

export default PersonalToday
