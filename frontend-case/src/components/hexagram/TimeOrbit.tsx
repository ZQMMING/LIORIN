import type { HeroStageValue } from '../../animation/hero'
import './TimeOrbit.css'

interface TimeOrbitProps {
  stage: HeroStageValue
  reducedMotion: boolean
}

const dots = [
  [140,28],[140,48],[140,68],[140,212],[140,232],[140,252],
  [28,140],[48,140],[68,140],[212,140],[232,140],[252,140],
  [88,88],[106,106],[174,174],[192,192],[192,88],[174,106],[106,174],[88,192],
  [140,125],[125,140],[140,140],[155,140],[140,155],
]

/** Visual metaphor only: no line is inferred without a backend hexagram contract. */
export default function TimeOrbit({ stage, reducedMotion }: TimeOrbitProps) {
  return <div className={'time-orbit-art' + (stage >= 3 || reducedMotion ? ' is-settled' : '')}>
    <svg viewBox="0 0 280 280" role="img" aria-label="河洛时间图形；卦象爻线等待数据提供">
      <circle className="orbit-ring" cx="140" cy="140" r="113" />
      <circle className="orbit-ring inner" cx="140" cy="140" r="86" />
      <path className="orbit-axis" d="M140 13v254M13 140h254" />
      <g className="orbit-dots">{dots.map(([cx,cy], i) =>
        <circle key={i} cx={cx} cy={cy} r={i > 19 ? 3.2 : 2.7} />)}</g>
      <circle className="orbit-center" cx="140" cy="140" r="12" />
      <circle className="orbit-core" cx="140" cy="140" r="3" />
    </svg>
  </div>
}
