import React from 'react'

/**
 * Error States — Section 28 of LIORIN spec
 */

interface ErrorStateProps {
  type: 'network' | 'calculation' | 'entitlement'
  onRetry?: () => void
}

const ErrorState: React.FC<ErrorStateProps> = ({ type, onRetry }) => {
  const configs = {
    network: {
      label: 'Network Error',
      title: '网络连接失败',
      message: '请检查网络后重试',
      showRetry: true,
    },
    calculation: {
      label: 'Calculation Error',
      title: '个人今日信息暂时无法计算',
      message: undefined,
      showRetry: true,
    },
    entitlement: {
      label: 'Entitlement Error',
      title: '此内容需要高级权限',
      message: '请升级至 Premium 以查看完整内容',
      showRetry: false,
    },
  }

  const cfg = configs[type]

  return (
    <section
      className="error-state"
      style={{
        padding: '48px 24px',
        textAlign: 'center',
        minHeight: '40vh',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
      }}
      role="alert"
      aria-live="assertive"
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
        {cfg.label}
      </div>
      <h2
        style={{
          fontFamily: 'var(--font-display)',
          fontSize: '18px',
          fontWeight: 400,
          color: 'var(--text-primary)',
          marginBottom: '8px',
        }}
      >
        {cfg.title}
      </h2>
      {cfg.message && (
        <p
          style={{
            fontSize: '13px',
            color: 'var(--text-secondary)',
            lineHeight: 1.6,
            marginBottom: '24px',
            maxWidth: '280px',
          }}
        >
          {cfg.message}
        </p>
      )}
      {cfg.showRetry && onRetry && (
        <button
          className="retry-btn"
          onClick={onRetry}
          style={{
            background: 'transparent',
            border: '1px solid var(--border-strong)',
            color: 'var(--text-primary)',
            fontFamily: 'var(--font-body)',
            fontSize: '10px',
            letterSpacing: '0.15em',
            textTransform: 'uppercase',
            cursor: 'pointer',
            padding: '10px 24px',
            transition: 'all 150ms ease',
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.background = 'var(--text-primary)'
            e.currentTarget.style.color = 'var(--bg-primary)'
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.background = 'transparent'
            e.currentTarget.style.color = 'var(--text-primary)'
          }}
        >
          重新加载
        </button>
      )}
    </section>
  )
}

export default ErrorState
