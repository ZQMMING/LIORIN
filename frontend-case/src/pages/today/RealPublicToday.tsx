import React, { useState, useEffect, useRef } from 'react'
import HetuLuoshuHero from '../../components/hexagram/HetuLuoshuHero'
import LoadingState from '../../components/feedback/LoadingState'
import ErrorState from '../../components/feedback/ErrorState'
import { playHeroAnimation, HeroStage, type HeroStageValue, BREATHING_CSS } from '../../animation/hero'
import type { RealPublicTodayView } from '../../view-models/publicToday'

interface RealPublicTodayProps {
  /** 真数据视图模型；loading/error 期间可为空 */
  view?: RealPublicTodayView | null
  isLoading?: boolean
  isError?: boolean
  onRetry?: () => void
}

/**
 * Public TODAY（真数据模式）— LIORIN_FRONTEND_SPEC_V2 §3 Step B
 *
 * 只渲染 GET /v1/today 真数据字段（干支三柱 / 卦名上下卦动爻变卦 / 宜忌 / 黄历要点）。
 * 不渲染 mock_until 字段（greeting/theme/guidance/reasoning）——后端无数据，
 * 前端不得用 mock 冒充。SVG 爻线渲染待后端 daily_hexagram 契约扩展后接入。
 */
const RealPublicToday: React.FC<RealPublicTodayProps> = ({
  view,
  isLoading = false,
  isError = false,
  onRetry,
}) => {
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

  if (isError || !view) {
    return <ErrorState type="network" onRetry={onRetry} />
  }

  return (
    <>
      <style>{BREATHING_CSS}</style>

      {/* Hero */}
      <section
        className="public-hero"
        aria-label="Public today"
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
          {heroStage > 0 ? '今日' : ''}
        </div>

        <HetuLuoshuHero stage={heroStage} prefersReducedMotion={prefersReducedMotion.current} />

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
          {view.hexName}
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
          {view.dateLabel}
        </div>

        <div
          style={{
            fontFamily: 'var(--font-display)',
            fontSize: '13px',
            color: 'var(--accent)',
            marginTop: '10px',
            textAlign: 'center',
            lineHeight: 1.8,
          }}
        >
          {view.hexUpper && view.hexLower && (
            <div>
              上卦 {view.hexUpper} · 下卦 {view.hexLower}
            </div>
          )}
          {view.movingLine && <div>动爻 {view.movingLine}</div>}
          {view.changedHex && <div>变卦 {view.changedHex}</div>}
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
        {/* 三柱干支 */}
        <div
          style={{
            display: 'flex',
            justifyContent: 'center',
            gap: '32px',
            marginBottom: '24px',
          }}
        >
          {view.pillars.map((p) => (
            <div key={p.label} style={{ textAlign: 'center' }}>
              <div
                style={{
                  fontFamily: 'var(--font-display)',
                  fontSize: '20px',
                  color: p.color || 'var(--text-primary)',
                }}
              >
                {p.name}
              </div>
              <div
                style={{
                  fontSize: '9px',
                  letterSpacing: '0.15em',
                  color: 'var(--text-muted)',
                  marginTop: '4px',
                }}
              >
                {p.label}
              </div>
            </div>
          ))}
        </div>

        <div style={{ width: '100%', height: '1px', background: 'var(--border)', margin: '24px 0' }} />

        {/* 宜 / 忌（真数据） */}
        <div style={{ display: 'flex', gap: '24px', marginBottom: '24px' }}>
          <div style={{ flex: 1 }}>
            <div
              style={{
                fontSize: '9px',
                letterSpacing: '0.2em',
                textTransform: 'uppercase',
                color: 'var(--text-muted)',
                marginBottom: '8px',
              }}
            >
              宜
            </div>
            {view.yi.length === 0 ? (
              <p style={{ fontSize: '12px', color: 'var(--text-muted)' }}>—</p>
            ) : (
              view.yi.map((item, i) => (
                <p
                  key={`yi-${i}`}
                  style={{ fontSize: '13px', color: 'var(--text-primary)', lineHeight: 1.9 }}
                >
                  {item}
                </p>
              ))
            )}
          </div>
          <div style={{ flex: 1 }}>
            <div
              style={{
                fontSize: '9px',
                letterSpacing: '0.2em',
                textTransform: 'uppercase',
                color: 'var(--text-muted)',
                marginBottom: '8px',
              }}
            >
              忌
            </div>
            {view.ji.length === 0 ? (
              <p style={{ fontSize: '12px', color: 'var(--text-muted)' }}>—</p>
            ) : (
              view.ji.map((item, i) => (
                <p
                  key={`ji-${i}`}
                  style={{ fontSize: '13px', color: 'var(--text-secondary)', lineHeight: 1.9 }}
                >
                  {item}
                </p>
              ))
            )}
          </div>
        </div>

        <div style={{ width: '100%', height: '1px', background: 'var(--border)', margin: '24px 0' }} />

        {/* 黄历要点 */}
        <div style={{ marginBottom: '24px' }}>
          <div
            style={{
              fontSize: '9px',
              letterSpacing: '0.2em',
              textTransform: 'uppercase',
              color: 'var(--text-muted)',
              marginBottom: '12px',
            }}
          >
            黄历
          </div>
          {view.essentials.map((row) => (
            <div
              key={row.label}
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                padding: '8px 0',
                borderBottom: '1px solid var(--border)',
              }}
            >
              <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>{row.label}</span>
              <span style={{ fontSize: '13px', color: 'var(--text-primary)' }}>{row.value}</span>
            </div>
          ))}
        </div>

        {/* CTA to create profile */}
        <div
          style={{
            marginTop: '32px',
            padding: '24px',
            borderTop: '1px solid var(--border)',
            textAlign: 'center',
          }}
        >
          <p
            style={{
              fontSize: '13px',
              color: 'var(--text-secondary)',
              lineHeight: 1.7,
              marginBottom: '16px',
            }}
          >
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

        {/* 溯源（真数据透明度） */}
        <p
          style={{
            fontSize: '10px',
            color: 'var(--text-muted)',
            textAlign: 'center',
            marginTop: '16px',
            fontFamily: 'var(--font-mono)',
          }}
        >
          trace: {view.traceId}
        </p>
      </section>
    </>
  )
}

export default RealPublicToday
