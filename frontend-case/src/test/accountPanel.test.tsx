import { afterEach, describe, expect, it, vi } from 'vitest'
import { cleanup, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import AccountPanel from '../components/account/AccountPanel'

vi.mock('../api/auth', () => ({
  loginWithPairing: vi.fn(), fetchMe: vi.fn(), logout: vi.fn(),
}))
vi.mock('../api/profile', () => ({
  saveStoredProfile: vi.fn(), readStoredProfile: vi.fn(),
}))
import { loginWithPairing, fetchMe } from '../api/auth'
import { saveStoredProfile } from '../api/profile'

const login = vi.mocked(loginWithPairing)
const me = vi.mocked(fetchMe)
const save = vi.mocked(saveStoredProfile)

afterEach(() => { cleanup(); vi.resetAllMocks() })

describe('账户与档案真实边界', () => {
  it('认证服务未装配时不能发起配对登录，不会自动建号', () => {
    render(<AccountPanel available={false} />)
    expect(screen.getByRole('button', { name: '设备配对登录' })).toBeDisabled()
    expect(screen.queryByRole('button', { name: '明确建号' })).not.toBeInTheDocument()
    expect(login).not.toHaveBeenCalled()
  })

  it('只有已认证且后端确认 stored=true 才提示保存成功', async () => {
    login.mockResolvedValueOnce({
      user_id: 'u-1', access_token: 'access', refresh_token: 'refresh',
      expires_in: 900, token_version: 1,
    })
    me.mockResolvedValueOnce({ user_id: 'u-1', is_new_user: false,
      has_birth_info: false, has_heluo_model: false, devices: [] })
    save.mockResolvedValueOnce({ profile_status: 'VALID', stored: true, trace_id: 'trace-1' })
    const user = userEvent.setup()
    render(<AccountPanel available />)
    await user.type(screen.getByLabelText('设备 ID'), 'dev-1')
    await user.type(screen.getByLabelText('配对码'), 'pair-1')
    await user.click(screen.getByRole('button', { name: '设备配对登录' }))
    expect(await screen.findByText('已登录账户')).toBeInTheDocument()
    await user.type(screen.getByLabelText('出生日期'), '1984-12-07')
    await user.type(screen.getByLabelText('出生小时（0–23）'), '16')
    await user.type(screen.getByLabelText('时区（IANA）'), 'Asia/Shanghai')
    await user.type(screen.getByLabelText('出生地'), 'Beijing')
    await user.type(screen.getByLabelText('当前城市'), 'Beijing')
    await user.click(screen.getByRole('button', { name: '保存档案' }))
    expect(await screen.findByText('档案已由后端确认保存。')).toBeInTheDocument()
    expect(save).toHaveBeenCalledTimes(1)
    expect(save.mock.calls[0][1]).toBe('access')
  })
})
