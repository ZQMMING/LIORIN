import React from 'react'

interface PremiumGateProps {
  onUnlock?: () => void
}

/**
 * Premium Gate — Section 22 of LIORIN spec
 */
const PremiumGate: React.FC<PremiumGateProps> = ({ onUnlock }) => {
  return (
    <section
      className="premium-gate"
      style={{
        padding: '32px 0',
        borderTop: '1px solid var(--border)',
        borderBottom: '1px solid var(--border)',
        marginBottom: '24px',
      }}
    >
      <div
        style={{
          fontSize: '9px',
          letterSpacing: '0.2em',
          textTransform: 'uppercase',
          color: 'var(--text-muted)',
          marginBottom: '12px',
        }}
      >
        Private
      </div>
      <h2
        style={{
          fontFamily: 'var(--font-display)',
          fontSize: '18px',
          fontWeight: 400,
          color: 'var(--text-primary)',
          marginBottom: '8px',
          lineHeight: 1.4,
        }}
      >
        深入了解你的时间结构
      </h2>
      <p
        style={{
          fontSize: '12px',
          color: 'var(--text-muted)',
          lineHeight: 1.6,
          marginBottom: '20px',
        }}
      >
        子平 · 五经 · 盲派 · 紫微 · 河洛 · 易经
      </p>
      <button
        className="premium-cta-btn"
        onClick={onUnlock}
        disabled={!onUnlock}
        style={{
          background: 'transparent',
          border: '1px solid var(--border-strong)',
          color: 'var(--text-primary)',
          fontFamily: 'var(--font-body)',
          fontSize: '10px',
          letterSpacing: '0.15em',
          textTransform: 'uppercase',
          cursor: onUnlock ? 'pointer' : 'not-allowed',
          opacity: onUnlock ? 1 : 0.55,
          padding: '12px 24px',
          transition: 'all 150ms ease',
        }}
        onMouseEnter={(e) => {
          e.currentTarget.style.background = 'var(--text-primary)'
          e.currentTarget.style.color = 'var(--bg-primary)'
          e.currentTarget.style.borderColor = 'var(--text-primary)'
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.background = 'transparent'
          e.currentTarget.style.color = 'var(--text-primary)'
          e.currentTarget.style.borderColor = 'var(--border-strong)'
        }}
        aria-label="解锁私享内容"
      >
        解锁私享
      </button>
      {!onUnlock && <p role="status">私享内容暂未开放。</p>}
    </section>
  )
}

export default PremiumGate
