import React from 'react'

/**
 * Loading State — Section 27 of LIORIN spec
 * Six faint yao lines forming progressively
 */
const LoadingState: React.FC<{ label?: string }> = ({ label = '正在整理今日信息' }) => {
  return (
    <div
      className="loading-state"
      style={{
        position: 'fixed',
        inset: 0,
        background: 'var(--bg-primary)',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 'var(--z-loading)',
        gap: '24px',
      }}
      role="status"
      aria-live="polite"
    >
      {/* Six yao lines loading animation */}
      <svg width="120" height="160" viewBox="0 0 120 160" aria-hidden="true">
        {[1, 2, 3, 4, 5, 6].map((i) => {
          const y = 10 + (i - 1) * 25
          const isYang = i % 2 === 1
          return (
            <g key={i} className="yao-loading-line">
              {isYang ? (
                <rect
                  x="20"
                  y={y}
                  width="80"
                  height="6"
                  fill="var(--text-primary)"
                  opacity="0.3"
                  rx="1"
                />
              ) : (
                <>
                  <rect
                    x="20"
                    y={y}
                    width="34"
                    height="6"
                    fill="var(--text-primary)"
                    opacity="0.3"
                    rx="1"
                  />
                  <rect
                    x="66"
                    y={y}
                    width="34"
                    height="6"
                    fill="var(--text-primary)"
                    opacity="0.3"
                    rx="1"
                  />
                </>
              )}
            </g>
          )
        })}
      </svg>
      <span
        style={{
          fontSize: '9px',
          letterSpacing: '0.2em',
          textTransform: 'uppercase',
          color: 'var(--text-muted)',
        }}
      >
        {label}
      </span>
    </div>
  )
}

export default LoadingState
