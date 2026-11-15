import React from 'react'
import type { Hexagram, YaoType, YaoPosition } from '../../mock/data'

interface SixDayCycleProps {
  hexagram: Hexagram
  activeYao: { position: YaoPosition; type: YaoType } | null
  cycleDay: number
  totalDays: number
  collapsed: boolean
  onToggle: () => void
}

/**
 * Six-Day Flow — Section 14 & 15 of LIORIN spec
 * Shows the 6-day cycle with active yao highlighted
 * Click to expand/collapse
 */
const SixDayCycle: React.FC<SixDayCycleProps> = ({
  hexagram,
  activeYao,
  cycleDay,
  totalDays,
  collapsed,
  onToggle,
}) => {
  const yaoNames = ['上爻', '五爻', '四爻', '三爻', '二爻', '初爻']
  const lineTypes = [...hexagram.lines].reverse() // top to bottom: 6,5,4,3,2,1

  return (
    <div className="six-day-cycle">
      <button
        onClick={onToggle}
        style={{
          background: 'none',
          border: 'none',
          color: 'var(--text-muted)',
          fontFamily: 'var(--font-body)',
          fontSize: '10px',
          letterSpacing: '0.15em',
          textTransform: 'uppercase',
          cursor: 'pointer',
          padding: '8px 0',
          width: '100%',
          textAlign: 'left',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          transition: 'color 150ms ease',
        }}
        onMouseEnter={(e) => (e.currentTarget.style.color = 'var(--text-secondary)')}
        onMouseLeave={(e) => (e.currentTarget.style.color = 'var(--text-muted)')}
        aria-expanded={!collapsed}
      >
        <span>六日流日卦</span>
        <span style={{ transition: 'transform 150ms ease', transform: collapsed ? 'rotate(-90deg)' : 'rotate(0deg)' }}>
          ▼
        </span>
      </button>

      {!collapsed && (
        <div className="cycle-details" style={{ padding: '8px 0 16px' }}>
          {/* Yao lines list */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', marginBottom: '16px' }}>
            {lineTypes.map((type, i) => {
              const position = (6 - i) as YaoPosition
              const isToday = activeYao?.position === position
              return (
                <div
                  key={position}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '12px',
                    padding: '4px 8px',
                    backgroundColor: isToday ? 'rgba(163,74,58,0.1)' : 'transparent',
                    borderRadius: '2px',
                    borderLeft: isToday ? '2px solid var(--accent)' : '2px solid transparent',
                  }}
                >
                  <span style={{
                    fontFamily: 'var(--font-mono)',
                    fontSize: '10px',
                    color: isToday ? 'var(--accent)' : 'var(--text-muted)',
                    minWidth: '20px',
                  }}>
                    {String(position).padStart(2, '0')}
                  </span>
                  {/* Mini yao line */}
                  {type === 'yang' ? (
                    <div style={{
                      width: '40px', height: '4px',
                      backgroundColor: isToday ? 'var(--accent)' : 'var(--text-secondary)',
                      borderRadius: '1px',
                    }} />
                  ) : (
                    <div style={{ display: 'flex', gap: '6px', width: '40px', alignItems: 'center' }}>
                      <div style={{
                        width: '17px', height: '4px',
                        backgroundColor: isToday ? 'var(--accent)' : 'var(--text-secondary)',
                        borderRadius: '1px',
                      }} />
                      <div style={{
                        width: '17px', height: '4px',
                        backgroundColor: isToday ? 'var(--accent)' : 'var(--text-secondary)',
                        borderRadius: '1px',
                      }} />
                    </div>
                  )}
                  <span style={{
                    fontFamily: 'var(--font-display)',
                    fontSize: '12px',
                    color: isToday ? 'var(--accent)' : 'var(--text-secondary)',
                  }}>
                    {yaoNames[i]}
                  </span>
                  {isToday && (
                    <span style={{
                      fontSize: '9px',
                      letterSpacing: '0.1em',
                      textTransform: 'uppercase',
                      color: 'var(--accent)',
                      marginLeft: 'auto',
                    }}>
                      TODAY
                    </span>
                  )}
                </div>
              )
            })}
          </div>

          {/* Cycle summary */}
          <div style={{
            borderTop: '1px solid var(--border)',
            paddingTop: '12px',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}>
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: '11px', color: 'var(--text-muted)' }}>
              {hexagram.name}
            </span>
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: '11px', color: 'var(--text-secondary)' }}>
              Day {cycleDay} / {totalDays}
            </span>
          </div>
        </div>
      )}
    </div>
  )
}

export default SixDayCycle
