import React from 'react'
import type { YaoType, YaoPosition } from '../../mock/data'

interface TodayYaoProps {
  position: YaoPosition
  type: YaoType
  classicalText: string
  modernText: string
  actions: string[]
}

/**
 * Today's Yao Card — Section 13 of LIORIN spec
 * Shows classical text, modern interpretation, and actionable guidance
 */
const TodayYao: React.FC<TodayYaoProps> = ({
  position,
  type,
  classicalText,
  modernText,
  actions,
}) => {
  const yaoNames = ['初爻', '二爻', '三爻', '四爻', '五爻', '上爻']
  const yaoName = yaoNames[position - 1]
  const typeLabel = type === 'yang' ? '阳爻' : '阴爻'

  return (
    <section className="today-yao-card" aria-label="今日之爻">
      <div
        style={{
          fontSize: '9px',
          letterSpacing: '0.2em',
          textTransform: 'uppercase',
          color: 'var(--text-muted)',
          marginBottom: '8px',
        }}
      >
        TODAY&apos;S YAO
      </div>

      <div style={{ display: 'flex', alignItems: 'baseline', gap: '12px', marginBottom: '16px' }}>
        <span
          style={{
            fontFamily: 'var(--font-display)',
            fontSize: '22px',
            fontWeight: 400,
            color: 'var(--text-primary)',
          }}
        >
          {yaoName}
        </span>
        <span
          style={{
            fontFamily: 'var(--font-mono)',
            fontSize: '11px',
            color: 'var(--text-muted)',
            letterSpacing: '0.05em',
          }}
        >
          {typeLabel}
        </span>
      </div>

      <div
        style={{
          width: '100%',
          height: '1px',
          background: 'var(--border)',
          marginBottom: '16px',
        }}
      />

      {/* Classical text */}
      {classicalText && (
        <div style={{ marginBottom: '12px' }}>
          <div
            style={{
              fontSize: '9px',
              letterSpacing: '0.2em',
              textTransform: 'uppercase',
              color: 'var(--text-muted)',
              marginBottom: '6px',
            }}
          >
            Classical
          </div>
          <p
            style={{
              fontFamily: 'var(--font-display)',
              fontSize: '14px',
              color: 'var(--text-secondary)',
              lineHeight: 1.7,
              fontStyle: 'italic',
            }}
          >
            {classicalText}
          </p>
        </div>
      )}

      {/* Modern interpretation */}
      {modernText && (
        <div style={{ marginBottom: '16px' }}>
          <div
            style={{
              fontSize: '9px',
              letterSpacing: '0.2em',
              textTransform: 'uppercase',
              color: 'var(--text-muted)',
              marginBottom: '6px',
            }}
          >
            Modern
          </div>
          <p
            style={{
              fontSize: '13px',
              color: 'var(--text-secondary)',
              lineHeight: 1.7,
            }}
          >
            {modernText}
          </p>
        </div>
      )}

      {/* Actions */}
      {actions.length > 0 && (
        <div>
          <div
            style={{
              fontSize: '9px',
              letterSpacing: '0.2em',
              textTransform: 'uppercase',
              color: 'var(--text-muted)',
              marginBottom: '10px',
            }}
          >
            今日行动
          </div>
          <ol style={{ listStyle: 'none', padding: 0, margin: 0, display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {actions.map((action, i) => (
              <li
                key={i}
                style={{
                  display: 'flex',
                  alignItems: 'flex-start',
                  gap: '12px',
                  fontSize: '13px',
                  color: 'var(--text-secondary)',
                  lineHeight: 1.6,
                }}
              >
                <span
                  style={{
                    fontFamily: 'var(--font-mono)',
                    fontSize: '10px',
                    color: 'var(--text-muted)',
                    minWidth: '18px',
                    paddingTop: '2px',
                  }}
                >
                  {String(i + 1).padStart(2, '0')}
                </span>
                <span>{action}</span>
              </li>
            ))}
          </ol>
        </div>
      )}
    </section>
  )
}

export default TodayYao
