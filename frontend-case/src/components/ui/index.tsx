import type { CSSProperties, HTMLAttributes, ButtonHTMLAttributes } from 'react'

type CardProps = HTMLAttributes<HTMLDivElement> & { variant?: 'glass' | 'gold'; hover?: boolean }
export function Card({ variant = 'glass', hover, style, ...props }: CardProps) {
  return <div {...props} style={{ padding: '20px', border: '1px solid var(--border)', background: 'var(--bg-elevated)', borderRadius: '8px', ...style }} data-variant={variant} data-hover={hover || undefined} />
}

type TagProps = HTMLAttributes<HTMLSpanElement> & { variant?: 'gold' | 'warning' | 'muted' | 'success' | 'accent'; size?: 'sm'; dot?: boolean }
export function Tag({ variant = 'muted', size, dot, style, children, ...props }: TagProps) {
  const tagStyle: CSSProperties = { display: 'inline-flex', alignItems: 'center', gap: 4, fontSize: 10, color: 'var(--text-secondary)', letterSpacing: '.08em', ...style }
  return <span {...props} style={tagStyle} data-variant={variant} data-size={size}>{dot && <span aria-hidden="true">•</span>}{children}</span>
}

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & { variant?: 'ghost'; size?: 'md' }
export function Button({ variant, size, style, ...props }: ButtonProps) {
  return <button type="button" {...props} data-variant={variant} data-size={size} style={{ background: 'transparent', border: '1px solid var(--border)', color: 'var(--text-primary)', padding: '10px 16px', ...style }} />
}
