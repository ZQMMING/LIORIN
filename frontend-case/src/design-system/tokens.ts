/**
 * LIORIN Design Tokens V1.0
 * Strictly follows 《LIORIN 前端工程总规范 V1.0》
 * Colors express UI state only — never 吉凶/好/坏/正/负
 */

export const tokens = {
  // Colors — UI state semantic only
  color: {
    bg: {
      primary: '#10100E',
      secondary: '#1A1A17',
      elevated: '#22221E',
    },
    text: {
      primary: '#F1EDE3',
      secondary: '#9B988F',
      muted: '#5C5A54',
    },
    accent: {
      cinnabar: '#A34A3A',
      ink: '#332C2B',
      paper: '#EEF3F2',
    },
    border: {
      default: 'rgba(241, 237, 227, 0.08)',
      strong: 'rgba(241, 237, 227, 0.15)',
    },
    state: {
      active: '#A34A3A',
      selected: '#F1EDE3',
      hover: 'rgba(241, 237, 227, 0.06)',
      disabled: '#5C5A54',
      error: '#A34A3A',
    },
  },

  // Typography
  font: {
    display: "'Noto Serif SC', Georgia, 'Times New Roman', serif",
    body: "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
    mono: "'JetBrains Mono', 'SF Mono', Consolas, monospace",
  },

  size: {
    xs: '9px',
    sm: '11px',
    md: '13px',
    lg: '16px',
    xl: '20px',
    '2xl': '26px',
    '3xl': '32px',
  },

  // Spacing
  space: {
    xs: '4px',
    sm: '8px',
    md: '16px',
    lg: '24px',
    xl: '32px',
    '2xl': '48px',
    '3xl': '64px',
  },

  // Border radius — zero-radius convention (Co-Star inspired)
  radius: {
    none: '0px',
    sm: '2px',
    md: '4px',
    lg: '8px',
    xl: '16px',
    hero: '24px',
  },

  // Motion
  motion: {
    fast: '150ms',
    normal: '250ms',
    breathing: '3200ms',
    ease: 'cubic-bezier(0.4, 0, 0.2, 1)',
    breathingEase: 'ease-in-out',
  },

  // Z-index scale
  z: {
    header: 10,
    nav: 20,
    modal: 100,
    loading: 200,
  },

  // Breakpoints
  breakpoint: {
    mobile: '375px',
    tablet: '768px',
    desktop: '1280px',
  },
} as const
