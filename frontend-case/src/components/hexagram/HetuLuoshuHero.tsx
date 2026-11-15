import React, { useEffect, useRef, useState } from 'react'
import type { HeroStageValue } from '../../animation/hero'
import { playHeroAnimation, HeroStage, STAGE_LABELS } from '../../animation/hero'

const SIZE = 280
const CX = SIZE / 2

interface HetuLuoshuHeroProps {
  stage: HeroStageValue
  prefersReducedMotion: boolean
}

/**
 * 河洛 Hero — Sections 10, 8 of LIORIN spec
 * Animates: 河图 → 洛书 → 数流动 → 数聚合 → 阴阳成形 → 六爻既立 → 卦象已成 → 今日之象
 */
const HetuLuoshuHero: React.FC<HetuLuoshuHeroProps> = ({ stage, prefersReducedMotion }) => {
  const [numbersVisible, setNumbersVisible] = useState(false)
  const [yaoLinesVisible, setYaoLinesVisible] = useState(false)
  const [hexagramVisible, setHexagramVisible] = useState(false)
  const [todayVisible, setTodayVisible] = useState(false)
  const [converged, setConverged] = useState(false)
  const prevStage = useRef<HeroStageValue>(0)

  useEffect(() => {
    const prev = prevStage.current
    const cur = stage

    if (prefersReducedMotion) {
      setNumbersVisible(true)
      setYaoLinesVisible(true)
      setHexagramVisible(true)
      setTodayVisible(true)
      setConverged(true)
      return
    }

    // Number labels appear at HETU_LUOSHU
    if (cur >= HeroStage.HETU_LUOSHU && !numbersVisible) {
      setNumbersVisible(true)
    }
    // Convergence at NUMBER_CONVERGENCE
    if (cur === HeroStage.NUMBER_CONVERGENCE && !converged) {
      setConverged(true)
    }
    if (cur < HeroStage.NUMBER_CONVERGENCE && converged) {
      setConverged(false)
    }
    // Yao lines at YAO_FORM
    if (cur >= HeroStage.YAO_FORM && !yaoLinesVisible) {
      setYaoLinesVisible(true)
    }
    if (cur < HeroStage.YAO_FORM && yaoLinesVisible) {
      setYaoLinesVisible(false)
    }
    // Hexagram at HEXAGRAM_FORM
    if (cur >= HeroStage.HEXAGRAM_FORM && !hexagramVisible) {
      setHexagramVisible(true)
    }
    if (cur < HeroStage.HEXAGRAM_FORM && hexagramVisible) {
      setHexagramVisible(false)
    }
    // Today reveal
    if (cur >= HeroStage.TODAY_REVEAL) {
      setTodayVisible(true)
    } else {
      setTodayVisible(false)
    }

    prevStage.current = cur
  }, [stage, prefersReducedMotion, numbersVisible, yaoLinesVisible, hexagramVisible, todayVisible, converged])

  // Hetu (河图) dot positions — 1-10 arranged in traditional pattern
  // Center cross: 5 white, outer: 1-4 yin (black), 6-10 yang (white)
  const hetuDots = [
    // 北: 1白 + 6黑
    { cx: CX, cy: 30, r: 5, type: 'yang', label: '1' },
    { cx: CX - 15, cy: 42, r: 4, type: 'yin', label: '6' },
    { cx: CX + 15, cy: 42, r: 4, type: 'yin', label: '6' },
    { cx: CX - 8, cy: 54, r: 4, type: 'yin', label: '6' },
    { cx: CX + 8, cy: 54, r: 4, type: 'yin', label: '6' },
    { cx: CX, cy: 62, r: 4, type: 'yin', label: '6' },
    // 南: 2黑 + 7白
    { cx: CX, cy: 238, r: 5, type: 'yin', label: '2' },
    { cx: CX, cy: 222, r: 4, type: 'yin', label: '2' },
    { cx: CX - 15, cy: 218, r: 4, type: 'yang', label: '7' },
    { cx: CX + 15, cy: 218, r: 4, type: 'yang', label: '7' },
    { cx: CX - 8, cy: 232, r: 4, type: 'yang', label: '7' },
    { cx: CX + 8, cy: 232, r: 4, type: 'yang', label: '7' },
    { cx: CX, cy: 244, r: 4, type: 'yang', label: '7' },
    // 东: 3白 + 8白
    { cx: 240, cy: CX, r: 5, type: 'yang', label: '3' },
    { cx: 220, cy: CX, r: 4, type: 'yang', label: '3' },
    { cx: 224, cy: CX - 15, r: 4, type: 'yang', label: '8' },
    { cx: 224, cy: CX + 15, r: 4, type: 'yang', label: '8' },
    { cx: 236, cy: CX - 8, r: 4, type: 'yang', label: '8' },
    { cx: 236, cy: CX + 8, r: 4, type: 'yang', label: '8' },
    { cx: 246, cy: CX - 15, r: 4, type: 'yang', label: '8' },
    { cx: 246, cy: CX + 15, r: 4, type: 'yang', label: '8' },
    // 西: 4黑 + 9黑
    { cx: 32, cy: CX, r: 5, type: 'yin', label: '4' },
    { cx: 52, cy: CX, r: 4, type: 'yin', label: '4' },
    { cx: 48, cy: CX - 15, r: 4, type: 'yin', label: '9' },
    { cx: 48, cy: CX + 15, r: 4, type: 'yin', label: '9' },
    { cx: 36, cy: CX - 8, r: 4, type: 'yin', label: '9' },
    { cx: 36, cy: CX + 8, r: 4, type: 'yin', label: '9' },
    { cx: 26, cy: CX - 15, r: 4, type: 'yin', label: '9' },
    { cx: 26, cy: CX + 15, r: 4, type: 'yin', label: '9' },
    { cx: 42, cy: CX, r: 4, type: 'yin', label: '9' },
    // 中心: 5白
    { cx: CX, cy: CX, r: 5, type: 'yang', label: '5' },
    { cx: CX, cy: CX - 18, r: 4, type: 'yang', label: '' },
    { cx: CX, cy: CX + 18, r: 4, type: 'yang', label: '' },
    { cx: CX - 18, cy: CX, r: 4, type: 'yang', label: '' },
    { cx: CX + 18, cy: CX, r: 4, type: 'yang', label: '' },
  ]

  // Luoshu (洛书) positions — 3×3 magic square: 492/357/816
  const luoshuPositions = [
    { cx: 70, cy: 60, value: '4' },
    { cx: CX, cy: 60, value: '9' },
    { cx: 200, cy: 60, value: '2' },
    { cx: 70, cy: CX, value: '3' },
    { cx: CX, cy: CX, value: '5' },
    { cx: 200, cy: CX, value: '7' },
    { cx: 70, cy: 210, value: '8' },
    { cx: CX, cy: 210, value: '1' },
    { cx: 200, cy: 210, value: '6' },
  ]

  // Converged positions (center cluster for convergence animation)
  const convergePositions = luoshuPositions.map((p) => ({
    ...p,
    cx: CX + (p.cx - CX) * 0.15,
    cy: CX + (p.cy - CX) * 0.15,
  }))

  // Yao lines for a sample hexagram (using the provided hexagram data later)
  const yaoYPositions = [55, 85, 115, 145, 175, 205]
  const yaoStartX = 60
  const yaoEndX = 210

  const isStageVisible = (minStage: HeroStageValue): boolean => stage >= minStage

  return (
    <svg
      width={SIZE}
      height={SIZE}
      viewBox={`0 0 ${SIZE} ${SIZE}`}
      role="img"
      aria-label="河洛卦象动画"
      style={{ width: '100%', maxWidth: '280px', height: 'auto' }}
    >
      <defs>
        <style>{`
          @keyframes liorin-pulse {
            0%, 100% { opacity: 0.6; }
            50% { opacity: 1; }
          }
          @keyframes liorin-converge {
            from { transform: translate(0, 0); }
            to { transform: translate(var(--dx), var(--dy)); }
          }
          .hetu-dot { transition: all 0.6s cubic-bezier(0.4, 0, 0.2, 1); }
          .luoshu-grid { transition: opacity 0.5s ease; }
          .yao-line { transition: opacity 0.4s ease; }
          .yao-line.visible { opacity: 1; }
          .yao-line.hidden { opacity: 0; }
          .number-label { transition: opacity 0.3s ease; }
          .number-label.visible { opacity: 1; }
          .number-label.hidden { opacity: 0; }
          .ring { transition: opacity 0.5s ease; }
        `}</style>
      </defs>

      {/* Background rings */}
      {[90, 70, 50, 30].map((r, i) => (
        <circle
          key={i}
          cx={CX}
          cy={CX}
          r={r}
          fill="none"
          stroke="rgba(163,74,58,0.15)"
          strokeWidth="0.5"
          className="ring"
          style={{ opacity: isStageVisible(HeroStage.HETU_LUOSHU) ? 0.3 + i * 0.05 : 0 }}
        />
      ))}

      {/* Cross guide lines */}
      {isStageVisible(HeroStage.HETU_LUOSHU) && (
        <>
          <line x1={CX} y1="10" x2={CX} y2={SIZE - 10} stroke="rgba(163,74,58,0.12)" strokeWidth="0.5" />
          <line x1="10" y1={CX} x2={SIZE - 10} y2={CX} stroke="rgba(163,74,58,0.12)" strokeWidth="0.5" />
        </>
      )}

      {/* 河图 dots */}
      {isStageVisible(HeroStage.HETU_LUOSHU) && stage < HeroStage.NUMBER_CONVERGENCE && (
        <g className="hetu-group">
          {hetuDots.map((dot, i) => {
            const isYang = dot.type === 'yang'
            const pulse = stage === HeroStage.NUMBER_FLOW
            return (
              <g key={i}>
                <circle
                  cx={dot.cx}
                  cy={dot.cy}
                  r={dot.r}
                  fill={isYang ? '#F1EDE3' : '#9B988F'}
                  opacity={pulse ? undefined : undefined}
                  style={{
                    transition: 'all 0.6s cubic-bezier(0.4, 0, 0.2, 1)',
                    animation: pulse ? 'liorin-pulse 1s ease-in-out infinite' : 'none',
                  }}
                />
                {dot.label && (
                  <text
                    x={dot.cx}
                    y={dot.cy + (isYang ? -dot.r - 4 : dot.r + 8)}
                    fill="#A34A3A"
                    fontSize="7"
                    fontWeight="500"
                    textAnchor="middle"
                    className={`number-label ${numbersVisible ? 'visible' : 'hidden'}`}
                    opacity={numbersVisible ? 0.8 : 0}
                  >
                    {dot.label}
                  </text>
                )}
              </g>
            )
          })}
        </g>
      )}

      {/* 洛书 grid */}
      {isStageVisible(HeroStage.NUMBER_CONVERGENCE) && (
        <g
          className="luoshu-grid"
          opacity={stage >= HeroStage.NUMBER_CONVERGENCE ? 1 : 0}
          style={{ transition: 'opacity 0.5s ease' }}
        >
          {/* Grid lines */}
          <rect x="60" y="55" width="150" height="150" fill="none" stroke="rgba(163,74,58,0.2)" strokeWidth="0.5" />
          {[85, 115, 145, 175].map((y) => (
            <line key={`h${y}`} x1="60" y1={y} x2="210" y2={y} stroke="rgba(163,74,58,0.15)" strokeWidth="0.5" />
          ))}
          {[85, 115, 145, 175].map((x) => (
            <line key={`v${x}`} x1={x} y1="55" x2={x} y2="205" stroke="rgba(163,74,58,0.15)" strokeWidth="0.5" />
          ))}
          {/* Numbers */}
          {luoshuPositions.map((p, i) => (
            <text
              key={i}
              x={p.cx}
              y={p.cy + 3}
              fill="#A34A3A"
              fontSize="10"
              fontWeight="500"
              textAnchor="middle"
              className="number-label visible"
              opacity={numbersVisible ? 0.9 : 0}
              style={{ transition: `opacity 0.3s ease ${i * 50}ms` }}
            >
              {p.value}
            </text>
          ))}
        </g>
      )}

      {/* Yao lines */}
      {isStageVisible(HeroStage.YAO_FORM) && (
        <g className="yao-group" opacity={yaoLinesVisible ? 1 : 0} style={{ transition: 'opacity 0.4s ease' }}>
          {yaoYPositions.map((y, i) => (
            <g key={i}>
              {/* Yang (solid) or Yin (broken) — sample hexagram for now */}
              {i % 2 === 0 ? (
                // Yang: solid line
                <rect
                  x={yaoStartX}
                  y={y}
                  width={yaoEndX - yaoStartX}
                  height="4"
                  fill="#F1EDE3"
                  opacity={0.9}
                  rx="1"
                  className={`yao-line ${yaoLinesVisible ? 'visible' : 'hidden'}`}
                  style={{ transitionDelay: `${i * 150}ms` }}
                />
              ) : (
                // Yin: broken line
                <>
                  <rect
                    x={yaoStartX}
                    y={y}
                    width={(yaoEndX - yaoStartX) * 0.42}
                    height="4"
                    fill="#F1EDE3"
                    opacity={0.9}
                    rx="1"
                    className={`yao-line ${yaoLinesVisible ? 'visible' : 'hidden'}`}
                    style={{ transitionDelay: `${i * 150}ms` }}
                  />
                  <rect
                    x={yaoStartX + (yaoEndX - yaoStartX) * 0.58}
                    y={y}
                    width={(yaoEndX - yaoStartX) * 0.42}
                    height="4"
                    fill="#F1EDE3"
                    opacity={0.9}
                    rx="1"
                    className={`yao-line ${yaoLinesVisible ? 'visible' : 'hidden'}`}
                    style={{ transitionDelay: `${i * 150}ms` }}
                  />
                </>
              )}
            </g>
          ))}
        </g>
      )}

      {/* Hexagram (final form) */}
      {isStageVisible(HeroStage.HEXAGRAM_FORM) && (
        <g
          opacity={hexagramVisible ? 1 : 0}
          style={{ transition: 'opacity 0.5s ease' }}
        >
          {yaoYPositions.map((y, i) => {
            const isYang = i % 2 === 0
            return isYang ? (
              <rect
                key={i}
                x={yaoStartX}
                y={y}
                width={yaoEndX - yaoStartX}
                height="5"
                fill="#F1EDE3"
                opacity="0.9"
                rx="1"
              />
            ) : (
              <g key={i}>
                <rect
                  x={yaoStartX}
                  y={y}
                  width={(yaoEndX - yaoStartX) * 0.42}
                  height="5"
                  fill="#F1EDE3"
                  opacity="0.9"
                  rx="1"
                />
                <rect
                  x={yaoStartX + (yaoEndX - yaoStartX) * 0.58}
                  y={y}
                  width={(yaoEndX - yaoStartX) * 0.42}
                  height="5"
                  fill="#F1EDE3"
                  opacity="0.9"
                  rx="1"
                />
              </g>
            )
          })}
        </g>
      )}

      {/* Stage indicator dots */}
      <g opacity={0.6}>
        {[0, 1, 2, 3, 4, 5, 6, 7, 8].map((i) => {
          const x = 80 + i * 16
          const isActive = stage === i
          const isDone = stage > i
          return (
            <circle
              key={i}
              cx={x}
              cy={SIZE - 12}
              r={isActive ? 3 : 2}
              fill={isActive ? '#A34A3A' : isDone ? 'rgba(241,237,227,0.4)' : 'rgba(241,237,227,0.15)'}
              style={{ transition: 'all 0.3s ease' }}
            />
          )
        })}
      </g>
    </svg>
  )
}

export default HetuLuoshuHero
