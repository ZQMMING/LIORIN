import { afterEach, describe, expect, it, vi } from 'vitest'
import { cleanup, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import App from '../App'

vi.mock('../api/today', () => ({ fetchToday: vi.fn().mockRejectedValue(new Error('offline')) }))
vi.mock('../api/authAvailability', () => ({ checkAuthAvailability: vi.fn().mockResolvedValue('available') }))
vi.mock('../api/auth', () => ({
  restoreBrowserSession: vi.fn().mockRejectedValue(new Error('no session')),
  requestEmailCode: vi.fn().mockResolvedValue({ status: 'sent_if_available' }),
  verifyEmailCode: vi.fn().mockResolvedValue({ user_id: 'u-1', access_token: 'access', refresh_token: 'refresh', expires_in: 900, token_version: 1 }),
  fetchMe: vi.fn().mockResolvedValue({ user_id: 'u-1' }), loginWithPairing: vi.fn(), logout: vi.fn(),
}))
vi.mock('../api/profile', () => ({
  saveStoredProfile: vi.fn().mockResolvedValue({ stored: true, profile_status: 'VALID' }),
  readStoredProfile: vi.fn(),
}))
vi.mock('../api/locations', () => ({ fetchBirthLocations: vi.fn().mockResolvedValue([{ id: 'CN_BEIJING', name: '北京', country: 'CN' }]) }))
vi.mock('../api/heluoToday', () => ({
  fetchPersonalHeluoToday: vi.fn().mockResolvedValue({ date: '2026-11-12', hexagram: '火水未济', upper: '离', lower: '坎', lines: [1, -1, 1, -1, 1, -1], active_yao_index: 2, period_start: '2026-11-10', period_end: '2026-11-14', period_days: 5, source: 'heluo_timeline_liuri', trace_id: 'TRACE-1' }),
}))

afterEach(() => { cleanup(); vi.clearAllMocks() })

describe('账户到个人今日的页面流程', () => {
  it('邮箱登录、保存出生资料后进入个人结果，返回账户仍保持登录', async () => {
    const user = userEvent.setup()
    render(<App />)
    await user.click(screen.getByRole('button', { name: '我的' }))
    await screen.findByText(/认证服务可用/)
    await user.type(screen.getByLabelText('邮箱'), 'user@example.com')
    await user.type(screen.getByLabelText('邮箱验证码'), '123456')
    await user.click(screen.getByRole('button', { name: '验证并登录' }))
    await screen.findByRole('heading', { name: '出生档案' })
    await user.type(screen.getByLabelText('出生日期'), '1980-06-22')
    await user.type(screen.getByLabelText('出生时间'), '12:30')
    await user.selectOptions(screen.getByLabelText('性别'), 'male')
    await user.type(screen.getByLabelText('出生地'), '北京')
    await user.click(await screen.findByRole('button', { name: /北京 · CN/ }))
    await user.click(screen.getByRole('button', { name: '保存档案' }))
    await user.click(await screen.findByRole('button', { name: '查看个人今日' }))
    expect(await screen.findByRole('heading', { name: '火水未济' })).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: '我的' }))
    expect(screen.getByRole('heading', { name: '出生档案' })).toBeInTheDocument()
  })
})
