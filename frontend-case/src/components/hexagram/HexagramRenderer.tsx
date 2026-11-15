import React, { useMemo } from 'react'
import type { Hexagram, YaoType, YaoPosition } from '../../mock/data'

interface HexagramProps {
  hexagram: Hexagram
  activeYao?: { position: YaoPosition; type: YaoType } | null
  size?: number
  interactive?: boolean
  onExpand?: () => void
}

/**
 * Hexagram Renderer — Section 12 of LIORIN spec
 * Data-driven SVG. Renders yang (solid) and yin (broken) yao lines.
 * Does NOT render meaning, judgment, or divination.
 */
const HexagramRenderer: React.FC<HexagramProps> = ({
  hexagram,
  activeYao,
  size = 200,
  interactive = false,
  onExpand,
}) => {
  const lineCount = 6
  const lineGap = 12
  const lineWidth = size * 0.6
  const lineStartX = (size - lineWidth) / 2
  const yaoHeight = 6
  const totalHeight = lineCount * (yaoHeight + lineGap) - lineGap
  const startY = (size - totalHeight) / 2

  // Lines array: index 0 = top (6th yao), index 5 = bottom (1st yao)
  const lines = useMemo(() => hexagram.lines, [hexagram.lines])

  const isActive = (position: YaoPosition): boolean =>
    activeYao?.position === position

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (interactive && (e.key === 'Enter' || e.key === ' ')) {
      e.preventDefault()
      onExpand?.()
    }
  }

  return (
    <svg
      width={size}
      height={size}
      viewBox={`0 0 ${size} ${size}`}
      role={interactive ? 'button' : 'img'}
      aria-label={`${hexagram.name} hexagram, ${hexagram.symbol}`}
      tabIndex={interactive ? 0 : undefined}
      onKeyDown={interactive ? handleKeyDown : undefined}
      onClick={interactive ? onExpand : undefined}
      style={{ cursor: interactive ? 'pointer' : 'default' }}
    >
      {/* Background ring (subtle) */}
      <circle
        cx={size / 2}
        cy={size / 2}
        r={size * 0.46}
        fill="none"
        stroke="rgba(241,237,227,0.06)"
        strokeWidth="0.5"
      />

      {lines.map((type: YaoType, i: number) => {
        const position = (lineCount - i) as YaoPosition // 6,5,4,3,2,1
        const y = startY + i * (yaoHeight + lineGap)
        const active = isActive(position)
        const isYang = type === 'yang'

        return (
          <g key={position}>
            {isYang ? (
              // Yang: solid line
              <rect
                x={lineStartX}
                y={y}
                width={lineWidth}
                height={yaoHeight}
                fill={active ? 'var(--accent)' : 'var(--text-primary)'}
                opacity={active ? 1 : 0.9}
                rx={1}
                className={active ? 'yao-active-breathing' : ''}
                style={active ? {
                  animation: 'liorin-breathing 3.2s ease-in-out infinite',
                  transformOrigin: 'center',
                } : {}}
              />
            ) : (
              // Yin: broken line (two segments)
              <>
                <rect
                  x={lineStartX}
                  y={y}
                  width={lineWidth * 0.42}
                  height={yaoHeight}
                  fill={active ? 'var(--accent)' : 'var(--text-primary)'}
                  opacity={active ? 1 : 0.9}
                  rx={1}
                  className={active ? 'yao-active-breathing' : ''}
                  style={active ? {
                    animation: 'liorin-breathing 3.2s ease-in-out infinite',
                    transformOrigin: 'center',
                  } : {}}
                />
                <rect
                  x={lineStartX + lineWidth * 0.58}
                  y={y}
                  width={lineWidth * 0.42}
                  height={yaoHeight}
                  fill={active ? 'var(--accent)' : 'var(--text-primary)'}
                  opacity={active ? 1 : 0.9}
                  rx={1}
                  className={active ? 'yao-active-breathing' : ''}
                  style={active ? {
                    animation: 'liorin-breathing 3.2s ease-in-out infinite',
                    transformOrigin: 'center',
                  } : {}}
                />
              </>
            )}
            {/* Today indicator arrow */}
            {active && (
              <g>
                <line
                  x1={lineStartX - 12}
                  y1={y + yaoHeight / 2}
                  x2={lineStartX - 4}
                  y2={y + yaoHeight / 2}
                  stroke="var(--accent)"
                  strokeWidth="1"
                  strokeLinecap="round"
                />
                <polygon
                  points={`${lineStartX - 4},${y + yaoHeight / 2 - 3} ${lineStartX - 4},${y + yaoHeight / 2 + 3} ${lineStartX - 8},${y + yaoHeight / 2}`}
                  fill="var(--accent)"
                />
              </g>
            )}
          </g>
        )
      })}
    </svg>
  )
}

export default HexagramRenderer
