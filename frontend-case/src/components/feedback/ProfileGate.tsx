import React from 'react'

/**
 * Profile Gate — Section 26 of LIORIN spec
 * Shows appropriate message based on profile status
 */

interface ProfileGateProps {
  status: 'NONE' | 'INSUFFICIENT' | 'CALCULATION_ERROR'
  onNext?: () => void
  onRetry?: () => void
}

const ProfileGate: React.FC<ProfileGateProps> = ({ status, onNext, onRetry }) => {
  const messages = {
    NONE: {
      title: '建立你的个人档案',
      subtitle: '你的个人时间结构尚未建立',
      cta: '完善资料',
    },
    INSUFFICIENT: {
      title: '还需要完善出生资料',
      subtitle: '请输入完整的出生日期、时间和地点',
      cta: '完善资料',
    },
    CALCULATION_ERROR: {
      title: '个人今日信息暂时无法计算',
      subtitle: undefined,
      cta: '重新加载',
    },
  }

  const msg = messages[status]

  return (
    <section
      className="profile-gate"
      style={{
        minHeight: '60vh',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '48px 24px',
        textAlign: 'center',
      }}
      aria-live="polite"
    >
      <div
        style={{
          fontSize: '9px',
          letterSpacing: '0.2em',
          textTransform: 'uppercase',
          color: 'var(--text-muted)',
          marginBottom: '16px',
        }}
      >
        Profile
      </div>
      <h2
        style={{
          fontFamily: 'var(--font-display)',
          fontSize: '22px',
          fontWeight: 400,
          color: 'var(--text-primary)',
          marginBottom: '12px',
          lineHeight: 1.4,
        }}
      >
        {msg.title}
      </h2>
      {msg.subtitle && (
        <p
          style={{
            fontSize: '13px',
            color: 'var(--text-secondary)',
            lineHeight: 1.7,
            maxWidth: '320px',
            marginBottom: '24px',
          }}
        >
          {msg.subtitle}
        </p>
      )}
      <button
        className="profile-cta-btn"
        onClick={status === 'CALCULATION_ERROR' ? onRetry : onNext}
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
          e.currentTarget.style.borderColor = 'var(--text-primary)'
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.background = 'transparent'
          e.currentTarget.style.color = 'var(--text-primary)'
          e.currentTarget.style.borderColor = 'var(--border-strong)'
        }}
      >
        {msg.cta}
      </button>
    </section>
  )
}

export default ProfileGate
