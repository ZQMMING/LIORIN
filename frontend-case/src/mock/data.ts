/**
 * MOCK DATA — LIORIN Frontend Case
 * Explicitly marked: MOCK ONLY, NOT PRODUCTION
 * Do NOT implement any calculation logic here.
 */

// ─── Entitlement States ───────────────────────────────────────────
export type Entitlement = 'PUBLIC' | 'AUTHENTICATED' | 'PREMIUM'
export type ProfileStatus = 'NONE' | 'INSUFFICIENT' | 'VALID' | 'CALCULATION_ERROR'

// ─── Yao Types ────────────────────────────────────────────────────
export type YaoType = 'yang' | 'yin'
export type YaoPosition = 1 | 2 | 3 | 4 | 5 | 6

// ─── Hexagram ─────────────────────────────────────────────────────
export interface Hexagram {
  id: string
  name: string        // e.g. "乾為天"
  symbol: string      // e.g. "䷀"
  lines: YaoType[]    // [6th, 5th, 4th, 3rd, 2nd, 1st] — top to bottom
}

// ─── Cycle (Six-Day Flow) ─────────────────────────────────────────
export interface Cycle {
  cycle_id: string
  hexagram_id: string
  start_date: string  // ISO date
  end_date: string
  cycle_day: number   // 1-6, comes from backend
  total_days: number  // always 6
}

// ─── Active Yao ───────────────────────────────────────────────────
export interface ActiveYao {
  yao_id: string
  position: YaoPosition
  type: YaoType
}

// ─── Today Data (what frontend consumes) ─────────────────────────
export interface TodayData {
  user_state: {
    entitlement: Entitlement
    profile_status: ProfileStatus
  }
  cycle: Cycle | null
  active_yao: ActiveYao | null
  hexagram: Hexagram | null
  yao_text: {
    classical: string   // 爻辞 from canonical evidence
    modern: string      // modern semantic from backend
  }
  guidance: {
    opportunity: string
    risk: string
    remediation: string
    actions: string[]
  }
  evidence: string      // classical reference
  date_label: string    // e.g. "2026.09.01 · 丙午年 戊申月 壬辰日"
}

// ─── Public Today Data (no personal info) ─────────────────────────
export interface PublicTodayData {
  hexagram: Hexagram
  date_label: string
  yao_text: {
    classical: string
    modern: string
  }
  guidance: {
    opportunity: string
    risk: string
    remediation: string
    actions: string[]
  }
  evidence: string
}

// ─── Mock: Public Today ───────────────────────────────────────────
export const MOCK_PUBLIC_TODAY: PublicTodayData = {
  hexagram: {
    id: 'zheng-zhen',
    name: '震為雷',
    symbol: '䷲',
    lines: ['yang', 'yang', 'yin', 'yin', 'yin', 'yin'] as YaoType[],
  },
  date_label: '2026.09.01 · 丙午年 戊申月 壬辰日',
  yao_text: {
    classical: '初九：出涕沱若，戚嗟若，吉。',
    modern: '今日气场初动，宜先观察再行动。微小的警觉会带来安稳。',
  },
  guidance: {
    opportunity: '整理与启动——完成搁置事项，为新阶段铺路',
    risk: '冒进扩张——今日不宜开启全新大型计划',
    remediation: '降速聚焦——将并行事项逐一关闭，留白给已完成的事',
    actions: [
      '清理桌面与文件，归档已完成事项',
      '确认本周前三项优先任务',
      '暂停新增项目，完成已有步骤',
    ],
  },
  evidence: '《震·初九》「初九：出涕沱若，戚嗟若，吉。」震卦初爻，阳气始动，宜戒慎。',
}

// ─── Mock: Personal Today (Day 3 of cycle) ───────────────────────
export const MOCK_PERSONAL_DAY3: TodayData = {
  user_state: {
    entitlement: 'AUTHENTICATED',
    profile_status: 'VALID',
  },
  cycle: {
    cycle_id: 'cy-20260901-001',
    hexagram_id: 'zheng-kun',
    start_date: '2026-08-28',
    end_date: '2026-09-02',
    cycle_day: 3,
    total_days: 6,
  },
  active_yao: {
    yao_id: 'yao-3-zheng-kun',
    position: 3,
    type: 'yin',
  },
  hexagram: {
    id: 'zheng-kun',
    name: '坤為地',
    symbol: '䷁',
    lines: ['yin', 'yin', 'yin', 'yin', 'yin', 'yin'] as YaoType[],
  },
  yao_text: {
    classical: '六三：含章可贞。或从王事，无成有终。',
    modern: '今日适合在既有框架内推进，不主动开创新局，但可在他人引领下完成要务。',
  },
  guidance: {
    opportunity: '承继执行——在已有路径上完成关键节点',
    risk: '独断专行——今日不宜单方面突破既定框架',
    remediation: '借势而行——寻找已有结构中的推动力',
    actions: [
      '完成上级交代的收尾工作',
      '参与团队讨论，提供执行建议而非主导',
      '记录进展，为下一周期做准备',
    ],
  },
  evidence: '《坤·六三》「六三：含章可贞。或从王事，无成有终。」',
  date_label: '2026.09.01 · 丙午年 戊申月 壬辰日',
}

// ─── Mock: Profile Gate (INSUFFICIENT) ───────────────────────────
export const MOCK_PROFILE_INSUFFICIENT: TodayData = {
  user_state: {
    entitlement: 'AUTHENTICATED',
    profile_status: 'INSUFFICIENT',
  },
  cycle: null as Cycle | null,
  active_yao: null as ActiveYao | null,
  hexagram: MOCK_PUBLIC_TODAY.hexagram,
  yao_text: MOCK_PUBLIC_TODAY.yao_text,
  guidance: MOCK_PUBLIC_TODAY.guidance,
  evidence: MOCK_PUBLIC_TODAY.evidence,
  date_label: MOCK_PUBLIC_TODAY.date_label,
}

// ─── Mock: Premium User ──────────────────────────────────────────
export const MOCK_PREMIUM: TodayData = {
  user_state: {
    entitlement: 'PREMIUM',
    profile_status: 'VALID',
  },
  cycle: MOCK_PERSONAL_DAY3.cycle,
  active_yao: MOCK_PERSONAL_DAY3.active_yao,
  hexagram: MOCK_PERSONAL_DAY3.hexagram,
  yao_text: {
    classical: '六三：含章可贞。或从王事，无成有终。',
    modern: '今日适合在既有框架内推进，不主动开创新局，但可在他人引领下完成要务。',
  },
  guidance: {
    opportunity: '承继执行——在已有路径上完成关键节点',
    risk: '独断专行——今日不宜单方面突破既定框架',
    remediation: '借势而行——寻找已有结构中的推动力',
    actions: [
      '完成上级交代的收尾工作',
      '参与团队讨论，提供执行建议而非主导',
      '记录进展，为下一周期做准备',
    ],
  },
  evidence: '《坤·六三》「六三：含章可贞。或从王事，无成有终。」',
  date_label: '2026.09.01 · 丙午年 戊申月 壬辰日',
}

// ─── Mock: Calculation Error ─────────────────────────────────────
export const MOCK_CALCULATION_ERROR: TodayData = {
  user_state: {
    entitlement: 'AUTHENTICATED',
    profile_status: 'CALCULATION_ERROR',
  },
  cycle: null as Cycle | null,
  active_yao: null as ActiveYao | null,
  hexagram: null as Hexagram | null,
  yao_text: { classical: '', modern: '' },
  guidance: { opportunity: '', risk: '', remediation: '', actions: [] },
  evidence: '',
  date_label: '2026.09.01 · 丙午年 戊申月 壬辰日',
}

// ─── Mock: All 64 Hexagrams (minimal) ────────────────────────────
export const ALL_HEXAGRAMS: Hexagram[] = [
  { id: 'zheng-qian', name: '乾為天', symbol: '䷀', lines: ['yang','yang','yang','yang','yang','yang'] },
  { id: 'zheng-kun', name: '坤為地', symbol: '䷁', lines: ['yin','yin','yin','yin','yin','yin'] },
  { id: 'zheng-zhen', name: '震為雷', symbol: '䷲', lines: ['yang','yin','yin','yin','yin','yin'] },
  { id: 'zheng-xun', name: '巽為風', symbol: '䷸', lines: ['yin','yang','yang','yang','yang','yang'] },
  { id: 'zheng-kan', name: '坎為水', symbol: '䷜', lines: ['yin','yang','yin','yin','yang','yin'] },
  { id: 'zheng-li', name: '離為火', symbol: '䷝', lines: ['yang','yin','yang','yang','yin','yang'] },
  { id: 'zheng-gen', name: '艮為山', symbol: '䷳', lines: ['yin','yin','yin','yang','yang','yang'] },
  { id: 'zheng-dui', name: '兌為澤', symbol: '䷹', lines: ['yang','yang','yin','yin','yin','yin'] },
]

// ─── i18n Keys ───────────────────────────────────────────────────
export const I18N = {
  nav: { today: '今日', guide: '指南', insights: '洞察', me: '我的' } as const,
  hero: { public: '今日之象', personal: '流日卦象' } as const,
  cycle: { day: '日', of: '／', cycle: '周期' } as const,
  yao: { today: '今日之爻', position: (n: number) => `${n}爻` } as const,
  state: { label: 'State', title: '状态' } as const,
  opportunity: { label: 'Opportunity', title: '机会' } as const,
  risk: { label: 'Risk', title: '风险' } as const,
  remediation: { label: 'Remediation', title: '建议' } as const,
  action: { label: 'Action', title: '行动' } as const,
  evidence: { label: 'Evidence', title: '依据' } as const,
  premium: { title: '私享', subtitle: '深入了解你的时间结构', cta: '解锁私享' } as const,
  profile: {
    none: '建立你的个人档案',
    insufficient: '还需要完善出生资料',
    valid: '个人今日信息',
    error: '个人今日信息暂时无法计算',
  } as const,
  loading: '正在整理今日信息',
  error: {
    network: '网络连接失败，请检查网络后重试',
    calculation: '个人今日信息暂时无法计算',
    entitlement: '此内容需要高级权限',
  } as const,
} as const
