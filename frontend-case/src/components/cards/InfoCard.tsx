import React from 'react'

interface InfoCardProps {
  label: string
  title: string
  text: string
  actionLabel?: string
  onAction?: () => void
  compact?: boolean
}

/**
 * Generic info card — used for Heluo, Yijing, Ziwei cards
 */
const InfoCard: React.FC<InfoCardProps> = ({
  label,
  title,
  text,
  actionLabel,
  onAction,
  compact = false,
}) => {
  return (
    <div
      className="info-card"
      style={{
        padding: compact ? '16px 0' : '20px 0',
        borderBottom: '1px solid var(--border)',
      }}
    >
      <div
        style={{
          fontSize: '9px',
          letterSpacing: '0.2em',
          textTransform: 'uppercase',
          color: 'var(--text-muted)',
          marginBottom: '8px',
        }}
      >
        {label}
      </div>
      <h3
        style={{
          fontFamily: 'var(--font-display)',
          fontSize: compact ? '15px' : '17px',
          fontWeight: 400,
          color: 'var(--text-primary)',
          marginBottom: compact ? '4px' : '8px',
          lineHeight: 1.4,
        }}
      >
        {title}
      </h3>
      {!compact && (
        <p
          style={{
            fontSize: '13px',
            color: 'var(--text-secondary)',
            lineHeight: 1.7,
            marginBottom: '12px',
          }}
        >
          {text}
        </p>
      )}
      {actionLabel && onAction && (
        <button
          className="card-action-btn"
          onClick={onAction}
          style={{
            background: 'none',
            border: 'none',
            color: 'var(--text-muted)',
            fontFamily: 'var(--font-body)',
            fontSize: '10px',
            letterSpacing: '0.15em',
            textTransform: 'uppercase',
            cursor: 'pointer',
            padding: '0',
            display: 'inline-flex',
            alignItems: 'center',
            gap: '6px',
            transition: 'color 150ms ease',
          }}
          onMouseEnter={(e) => (e.currentTarget.style.color = 'var(--text-primary)')}
          onMouseLeave={(e) => (e.currentTarget.style.color = 'var(--text-muted)')}
          aria-label={actionLabel}
        >
          {actionLabel}
          <span aria-hidden="true">→</span>
        </button>
      )}
    </div>
  )
}

export default InfoCard
