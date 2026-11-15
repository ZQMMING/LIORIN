/**
 * Animation System — Hero State Machine
 * Section 10 of LIORIN spec: full entrance animation sequence
 * Section 8: breathing yao animation规范
 */

export const HeroStage = {
  IDLE: 0,
  HETU_LUOSHU: 1,
  NUMBER_FLOW: 2,
  NUMBER_CONVERGENCE: 3,
  YIN_YANG_FORM: 4,
  YAO_FORM: 5,
  HEXAGRAM_FORM: 6,
  HEXAGRAM_HOLD: 7,
  TODAY_REVEAL: 8,
} as const

export type HeroStageKey = keyof typeof HeroStage
export type HeroStageValue = (typeof HeroStage)[HeroStageKey]

export const STAGE_LABELS: Record<HeroStageValue, string> = {
  [HeroStage.IDLE]: '準備就緒',
  [HeroStage.HETU_LUOSHU]: '河洛有象',
  [HeroStage.NUMBER_FLOW]: '數聚成氣',
  [HeroStage.NUMBER_CONVERGENCE]: '數收陰陽',
  [HeroStage.YIN_YANG_FORM]: '陰陽成形',
  [HeroStage.YAO_FORM]: '六爻既立',
  [HeroStage.HEXAGRAM_FORM]: '卦象已成',
  [HeroStage.HEXAGRAM_HOLD]: '靜觀其變',
  [HeroStage.TODAY_REVEAL]: '今日之象',
}

export const STAGE_DURATIONS: Record<HeroStageValue, number> = {
  [HeroStage.IDLE]: 0,
  [HeroStage.HETU_LUOSHU]: 1000,
  [HeroStage.NUMBER_FLOW]: 1000,
  [HeroStage.NUMBER_CONVERGENCE]: 900,
  [HeroStage.YIN_YANG_FORM]: 450,
  [HeroStage.YAO_FORM]: 900,
  [HeroStage.HEXAGRAM_FORM]: 700,
  [HeroStage.HEXAGRAM_HOLD]: 1000,
  [HeroStage.TODAY_REVEAL]: 500,
} as const

export function delay(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

export async function playHeroAnimation(
  onStageChange: (stage: HeroStageValue) => void,
  prefersReducedMotion: boolean
): Promise<void> {
  if (prefersReducedMotion) {
    // Skip to final state
    onStageChange(HeroStage.TODAY_REVEAL)
    return
  }

  const stages: HeroStageValue[] = [
    HeroStage.HETU_LUOSHU,
    HeroStage.NUMBER_FLOW,
    HeroStage.NUMBER_CONVERGENCE,
    HeroStage.YIN_YANG_FORM,
    HeroStage.YAO_FORM,
    HeroStage.HEXAGRAM_FORM,
    HeroStage.HEXAGRAM_HOLD,
    HeroStage.TODAY_REVEAL,
  ]

  for (const stage of stages) {
    onStageChange(stage)
    await delay(STAGE_DURATIONS[stage])
  }
}

/**
 * Breathing animation for active yao
 * Section 8 spec: 3.2s duration, ease-in-out, subtle scale 1.000→1.015→1.000
 */
export const BREATHING_CSS = `
  @keyframes liorin-breathing {
    0%, 100% {
      opacity: 0.85;
      transform: scale(1);
    }
    50% {
      opacity: 1;
      transform: scale(1.015);
    }
  }

  .yao-active-breathing {
    animation: liorin-breathing var(--motion-breathing) var(--motion-breathing-ease) infinite;
    transform-origin: center;
  }

  @media (prefers-reduced-motion: reduce) {
    .yao-active-breathing {
      animation: none;
      opacity: 1;
    }
  }
`

/**
 * Loading animation — six yao lines forming progressively
 * Section 27: Loading is LIORIN brand language
 */
export const LOADING_CSS = `
  @keyframes liorin-yao-appear {
    from { opacity: 0; transform: scaleX(0.3); }
    to { opacity: 1; transform: scaleX(1); }
  }

  .yao-loading-line {
    opacity: 0;
    animation: liorin-yao-appear 0.4s ease forwards;
  }

  .yao-loading-line:nth-child(1) { animation-delay: 0ms; }
  .yao-loading-line:nth-child(2) { animation-delay: 120ms; }
  .yao-loading-line:nth-child(3) { animation-delay: 240ms; }
  .yao-loading-line:nth-child(4) { animation-delay: 360ms; }
  .yao-loading-line:nth-child(5) { animation-delay: 480ms; }
  .yao-loading-line:nth-child(6) { animation-delay: 600ms; }

  @media (prefers-reduced-motion: reduce) {
    .yao-loading-line {
      animation: none;
      opacity: 1;
    }
  }
`
