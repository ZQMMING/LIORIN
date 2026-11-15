import React, { useState, useEffect, useRef } from 'react'
import HexagramRenderer from '../../components/hexagram/HexagramRenderer'
import HetuLuoshuHero from '../../components/hexagram/HetuLuoshuHero'
import TodayYao from '../../components/yao/TodaysYao'
import LoadingState from '../../components/feedback/LoadingState'
import ErrorState from '../../components/feedback/ErrorState'
import PremiumGate from '../../components/premium/PremiumGate'
import { playHeroAnimation, HeroStage, type HeroStageValue, BREATHING_CSS } from '../../animation/hero'
import type { PublicTodayData } from '../../mock/data'

interface PublicTodayProps {
  data: PublicTodayData
  isLoading?: boolean
  onRetry?: () => void
}

/**
 * Public TODAY page — Section 2 of LIORIN spec
 * No personal info, no cycle day, no active yao
 */
const PublicToday: React.FC<PublicTodayProps> = ({ data, isLoading = false, onRetry }) => {
  const [heroStage, setHeroStage] = useState<HeroStageValue>(0 as HeroStageValue)
  const prefersReducedMotion = useRef(
    window.matchMedia('(prefers-reduced-motion: reduce)').matches
  )

  useEffect(() => {
    playHeroAnimation(setHeroStage, prefersReducedMotion.current)
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  if (isLoading) {
    return <LoadingState />
  }

  if (!data.hexagram) {
    return <ErrorState type="network" onRetry={onRetry} />
  }

  const { hexagram, yao_text, guidance, evidence, date_label } = data

  return (
    <>
      <style>{BREATHING_CSS}</style>

      {/* Hero */}
      <section
        className="public-hero"
        aria-label="Public today hexagram"
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
        <div
          style={{
            position: 'absolute',
            top: '24px',
            fontSize: '9px',
            letterSpacing: '0.2em',
            textTransform: 'uppercase',
            color: heroStage > 0 ? 'var(--text-secondary)' : 'var(--text-muted)',
          }}
        >
          {heroStage > 0 ? '今日之象' : ''}
        </div>

        {/* Hero: 河洛 animation during stages 0-7, static hexagram at stage 8 */}
        {heroStage < HeroStage.TODAY_REVEAL ? (
          <HetuLuoshuHero stage={heroStage} prefersReducedMotion={prefersReducedMotion.current} />
        ) : (
          <HexagramRenderer hexagram={hexagram} size={200} />
        )}

        <h1
          style={{
            fontFamily: 'var(--font-display)',
            fontSize: '24px',
            fontWeight: 400,
            color: 'var(--text-primary)',
            marginTop: '24px',
            textAlign: 'center',
            lineHeight: 1.4,
          }}
        >
          {guidance.opportunity || '今日之象'}
        </h1>

        <div
          style={{
            fontFamily: 'var(--font-mono)',
            fontSize: '11px',
            letterSpacing: '0.1em',
            color: 'var(--text-muted)',
            marginTop: '12px',
            textAlign: 'center',
          }}
        >
          {date_label}
        </div>

        <div
          style={{
            fontFamily: 'var(--font-display)',
            fontSize: '14px',
            color: 'var(--accent)',
            marginTop: '8px',
          }}
        >
          {hexagram.symbol} {hexagram.name}
        </div>
      </section>

      {/* Content */}
      <section
        className="public-content"
        style={{
          maxWidth: '640px',
          margin: '0 auto',
          padding: '0 24px 48px',
        }}
      >
        <div style={{ width: '100%', height: '1px', background: 'var(--border)', margin: '24px 0' }} />

        {/* Today's Yao (public version — no cycle info) */}
        <TodayYao
          position={3} // default, no active yao in public
          type={hexagram.lines[2] || 'yin'}
          classicalText={yao_text.classical}
          modernText={yao_text.modern}
          actions={guidance.actions}
        />

        <div style={{ width: '100%', height: '1px', background: 'var(--border)', margin: '24px 0' }} />

        {/* Guidance cards */}
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
            {guidance.remediation}
          </p>
        </div>

        <PremiumGate />

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

        {/* CTA to create profile */}
        <div style={{
          marginTop: '32px',
          padding: '24px',
          borderTop: '1px solid var(--border)',
          textAlign: 'center',
        }}>
          <p style={{
            fontSize: '13px', color: 'var(--text-secondary)', lineHeight: 1.7,
            marginBottom: '16px',
          }}>
            建立个人档案，获取基于你出生时间的专属流日卦
          </p>
          <button
            style={{
              background: 'transparent',
              border: '1px solid var(--border-strong)',
              color: 'var(--text-primary)',
              fontFamily: 'var(--font-body)',
              fontSize: '10px',
              letterSpacing: '0.15em',
              textTransform: 'uppercase',
              cursor: 'pointer',
              padding: '12px 28px',
              transition: 'all 150ms ease',
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.background = 'var(--text-primary)'
              e.currentTarget.style.color = 'var(--bg-primary)'
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.background = 'transparent'
              e.currentTarget.style.color = 'var(--text-primary)'
            }}
          >
            建立档案
          </button>
        </div>
      </section>
    </>
  )
}

export default PublicToday
