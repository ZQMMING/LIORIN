import React from 'react'
import HexagramRenderer from './HexagramRenderer'
import type { Hexagram, ActiveYao } from '../../mock/data'

interface FlowHexagramProps {
  hexagram: Hexagram
  activeYao: ActiveYao | null
  cycleDay: number
  totalDays: number
  onExpand?: () => void
  expanded?: boolean
}

/**
 * Personal Flow Hexagram — Section 6 of LIORIN spec
 * Hero element showing hexagram + today yao + cycle position
 */
const FlowHexagram: React.FC<FlowHexagramProps> = ({
  hexagram,
  activeYao,
  cycleDay,
  totalDays,
  onExpand,
  expanded,
}) => {
  return (
    <div
      className="flow-hexagram"
      style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '16px' }}
    >
      <HexagramRenderer
        hexagram={hexagram}
        activeYao={activeYao}
        size={200}
        interactive={!!onExpand}
        onExpand={onExpand}
      />

      {/* Cycle day indicator */}
      <div className="cycle-indicator" style={{ textAlign: 'center' }}>
        <div
          style={{
            fontSize: '11px',
            letterSpacing: '0.15em',
            textTransform: 'uppercase',
            color: 'var(--text-muted)',
            marginBottom: '4px',
          }}
        >
          Day {cycleDay} / {totalDays}
        </div>
        {activeYao && (
          <div
            style={{
              fontFamily: 'var(--font-display)',
              fontSize: '14px',
              color: 'var(--accent)',
            }}
          >
            {['初爻','二爻','三爻','四爻','五爻','上爻'][activeYao.position - 1]}
            {' · '}今日之爻
          </div>
        )}
      </div>

      {/* Hexagram name */}
      <div
        style={{
          fontFamily: 'var(--font-display)',
          fontSize: '18px',
          color: 'var(--text-primary)',
          letterSpacing: '0.05em',
        }}
      >
        {hexagram.name}
      </div>

      {onExpand && (
        <button
          className="expand-btn"
          onClick={onExpand}
          style={{
            background: 'none',
            border: 'none',
            color: 'var(--text-muted)',
            fontFamily: 'var(--font-body)',
            fontSize: '10px',
            letterSpacing: '0.15em',
            textTransform: 'uppercase',
            cursor: 'pointer',
            padding: '4px 0',
            transition: 'color 150ms ease',
          }}
          onMouseEnter={(e) => (e.currentTarget.style.color = 'var(--text-primary)')}
          onMouseLeave={(e) => (e.currentTarget.style.color = 'var(--text-muted)')}
          aria-expanded={expanded}
          aria-label={expanded ? '收起六日流日卦' : '展开六日流日卦'}
        >
          {expanded ? '收起' : '展开'}
        </button>
      )}
    </div>
  )
}

export default FlowHexagram
