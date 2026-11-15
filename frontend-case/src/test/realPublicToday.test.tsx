/**
 * RealPublicToday 契约/行为测试 — LIORIN_FRONTEND_SPEC_V2 §3 Step B
 *
 * 锁定：
 * 1. buildRealPublicTodayView 只映射真数据字段（不消费 mock_until 字段）
 * 2. daily_hexagram.name 缺失时 FAIL FAST（不静默兜底）
 * 3. 组件渲染真数据（卦名/宜忌/黄历要点），loading/error 态正确切换
 */
import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { buildRealPublicTodayView } from '../view-models/publicToday'
import type { TodayResponse } from '../contracts/today'
import RealPublicToday from '../pages/today/RealPublicToday'

const FIXTURE: TodayResponse = {
  ganZhi: [
    { name: '丙午', label: '年柱', color: 'var(--c-huo)' },
    { name: '己亥', label: '月柱', color: 'var(--c-shui)' },
    { name: '庚辰', label: '日柱', color: 'var(--c-jin)' },
  ],
  weekday: '星期四',
  day: 12,
  lunarMonth: '十月',
  yi: ['祭祀', '出行'],
  ji: ['动土'],
  calendar: {
    solar_date: '2026.11.12',
    day_stem: '庚',
    day_branch: '辰',
    year_ganzhi: '丙午',
    month_ganzhi: '己亥',
    day_ganzhi: '庚辰',
    lunar_month: '十',
    lunar_day: '初三',
    lunar_month_label: '十月初三',
    jie_qi: '立冬',
    prev_jie_qi: { name: '霜降', date: '2026-10-23' },
    next_jie_qi: { name: '小雪', date: '2026-11-22' },
    jianchu: '收',
    zhishen: '天德',
    zhishen_type: '吉神',
    zhishen_luck: '吉',
    xiushu: '张',
    xiushu_luck: '吉',
    chong: '狗',
    chong_shengxiao: '狗',
    sha: '南',
    sheng_xiao: '马',
    nian_na_yin: '天河水',
    month_na_yin: '平地木',
    day_na_yin: '白蜡金',
    peng_zu_gan: '庚不理',
    peng_zu_zhi: '辰不哭',
    position_xi: '西北',
    position_fu: '西南',
    position_cai: '正东',
    daily_hexagram: {
      name: '火水未济',
      upper: '火',
      lower: '水',
      moving_line: '九二',
      changed: '火风鼎',
    },
    yi: ['祭祀', '出行'],
    ji: ['动土'],
    ji_xiang: [],
    xiong_sha: [],
    source_ids: ['HL-001'],
  },
  provenance: {
    ganZhi: 'computed',
    weekday: 'computed',
    day: 'computed',
    'lunarMonth/yi/ji/calendar': 'computed',
    'greeting/monthLabel/theme/catalyst/dimensions/time_window/hexagram/reasoning/cross_validation':
      'mock_until_profile_gate_or_content_module',
  },
  trace_id: 'TRACE-TEST-001',
}

describe('buildRealPublicTodayView', () => {
  it('映射真数据字段：日期行/卦象/宜忌/三柱/黄历要点', () => {
    const v = buildRealPublicTodayView(FIXTURE)
    expect(v.dateLabel).toBe('2026.11.12 · 丙午年 己亥月 庚辰日')
    expect(v.hexName).toBe('火水未济')
    expect(v.hexUpper).toBe('火')
    expect(v.hexLower).toBe('水')
    expect(v.movingLine).toBe('九二')
    expect(v.changedHex).toBe('火风鼎')
    expect(v.yi).toEqual(['祭祀', '出行'])
    expect(v.ji).toEqual(['动土'])
    expect(v.pillars).toHaveLength(3)
    expect(v.pillars[2]).toEqual({ name: '庚辰', label: '日柱', color: 'var(--c-jin)' })
    const labels = v.essentials.map((r) => r.label)
    expect(labels).toContain('农历')
    expect(labels).toContain('节气')
    expect(labels).toContain('建除')
    expect(labels).toContain('冲煞')
    expect(v.traceId).toBe('TRACE-TEST-001')
  })

  it('FAIL FAST：daily_hexagram.name 缺失时抛错，不静默兜底', () => {
    const broken = JSON.parse(JSON.stringify(FIXTURE)) as TodayResponse
    // @ts-expect-error 故意破坏契约
    broken.calendar.daily_hexagram = { upper: '火', lower: '水' }
    expect(() => buildRealPublicTodayView(broken)).toThrow(/FAIL FAST|daily_hexagram/)
  })

  it('不消费 mock_until 字段：视图模型不含 guidance/reasoning/yao_text', () => {
    const v = buildRealPublicTodayView(FIXTURE)
    const record = v as unknown as Record<string, unknown>
    expect(record).not.toHaveProperty('guidance')
    expect(record).not.toHaveProperty('reasoning')
    expect(record).not.toHaveProperty('yaoText')
    expect(record).not.toHaveProperty('evidence')
  })
})

describe('RealPublicToday 组件', () => {
  it('渲染真数据：卦名/宜/忌/黄历要点可见', () => {
    const v = buildRealPublicTodayView(FIXTURE)
    render(<RealPublicToday view={v} />)
    expect(screen.getByText('火水未济')).toBeInTheDocument()
    expect(screen.getByText('祭祀')).toBeInTheDocument()
    expect(screen.getByText('动土')).toBeInTheDocument()
    expect(screen.getByText('动爻 九二')).toBeInTheDocument()
    expect(screen.getByText('变卦 火风鼎')).toBeInTheDocument()
    expect(screen.getByText(/TRACE-TEST-001/)).toBeInTheDocument()
    // 黄历要点行
    expect(screen.getByText('立冬')).toBeInTheDocument()
  })

  it('loading 态不渲染真数据内容', () => {
    render(<RealPublicToday view={null} isLoading />)
    expect(screen.queryByText('火水未济')).not.toBeInTheDocument()
  })

  it('error 态显示错误外壳并提供重试', async () => {
    const onRetry = vi.fn()
    render(<RealPublicToday view={null} isError onRetry={onRetry} />)
    const alert = screen.getByRole('alert')
    expect(alert).toBeInTheDocument()
    const retry = screen.getByRole('button', { name: /重新加载/ })
    await userEvent.click(retry)
    expect(onRetry).toHaveBeenCalled()
  })
})
