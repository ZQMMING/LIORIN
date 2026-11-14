import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { cleanup, render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import AccountPanel from '../components/account/AccountPanel'
import { ApiClientError } from '../api/http'

vi.mock('../api/auth', () => ({
  loginWithPairing: vi.fn(), fetchMe: vi.fn(), logout: vi.fn(),
  requestEmailCode: vi.fn(), verifyEmailCode: vi.fn(),
}))
vi.mock('../api/profile', () => ({
  saveStoredProfile: vi.fn(), readStoredProfile: vi.fn(),
}))
vi.mock('../api/locations', () => ({ fetchBirthLocations: vi.fn() }))
import { fetchBirthLocations } from '../api/locations'
import { loginWithPairing, fetchMe, logout, requestEmailCode, verifyEmailCode } from '../api/auth'
import { saveStoredProfile, readStoredProfile } from '../api/profile'

const login = vi.mocked(loginWithPairing)
const me = vi.mocked(fetchMe)
const save = vi.mocked(saveStoredProfile)
const requestCode = vi.mocked(requestEmailCode)
const verifyCode = vi.mocked(verifyEmailCode)

afterEach(() => { cleanup(); vi.resetAllMocks() })
beforeEach(() => { vi.mocked(fetchBirthLocations).mockResolvedValue([{ id: 'CN_BEIJING', name: '北京', country: 'CN' }]) })

describe('账户与档案真实边界', () => {
  it('退出服务失败时仍清除本页会话并说明撤销未确认', async () => {
    vi.mocked(logout).mockRejectedValueOnce(new Error('offline'))
    const onSessionChange = vi.fn()
    render(<AccountPanel available onSessionChange={onSessionChange} session={{ user_id: 'u-1', access_token: 'access', refresh_token: 'refresh', expires_in: 900, token_version: 1 }} />)
    await userEvent.click(screen.getByRole('button', { name: '退出' }))
    expect(onSessionChange).toHaveBeenCalledWith(null)
    expect(screen.queryByRole('heading', { name: '出生档案' })).not.toBeInTheDocument()
    expect(await screen.findByText('本页面已退出；服务器未确认撤销原会话。')).toBeInTheDocument()
  })
  it('读取已存档案后可直接查看个人今日，修改后需重新保存', async () => {
    vi.mocked(readStoredProfile).mockResolvedValueOnce({ birth_date: '1984-12-07', birth_time: { hour: 16, minute: 30 }, gender: 'male', location: 'CN_BEIJING', timezone: 'Asia/Shanghai', calendar_system: 'solar' })
    const onProfileReady = vi.fn()
    const user = userEvent.setup()
    render(<AccountPanel available onProfileReady={onProfileReady} session={{ user_id: 'u-1', access_token: 'access', refresh_token: 'refresh', expires_in: 900, token_version: 1 }} />)
    await user.click(screen.getByRole('button', { name: '读取已存档案' }))
    await user.click(await screen.findByRole('button', { name: '查看个人今日' }))
    expect(onProfileReady).toHaveBeenCalledOnce()
    await user.clear(screen.getByLabelText('出生时间'))
    expect(screen.queryByRole('button', { name: '查看个人今日' })).not.toBeInTheDocument()
  })
  it('旧档案的城市别名可搜索并重新选择', async () => {
    vi.mocked(fetchBirthLocations).mockResolvedValueOnce([{ id: 'CN_BEIJING', name: '北京', country: 'CN', aliases: ['Beijing'] }])
    vi.mocked(readStoredProfile).mockResolvedValueOnce({ birth_date: '1984-12-07', birth_time: { hour: 16, minute: 30 }, gender: 'male', location: 'Beijing', timezone: 'Asia/Shanghai', calendar_system: 'solar' })
    const user = userEvent.setup()
    render(<AccountPanel available session={{ user_id: 'u-1', access_token: 'access', refresh_token: 'refresh', expires_in: 900, token_version: 1 }} />)
    await user.click(screen.getByRole('button', { name: '读取已存档案' }))
    expect(await screen.findByDisplayValue('Beijing')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: '保存档案' })).toBeDisabled()
    await user.click(screen.getByLabelText('出生地'))
    await user.click(await screen.findByRole('button', { name: /北京 · CN/ }))
    expect(screen.getByLabelText('出生地')).toHaveValue('北京 · CN')
    expect(screen.getByRole('button', { name: '保存档案' })).toBeEnabled()
  })
  it('没有已存档案时提示填写，保留当前输入', async () => {
    vi.mocked(readStoredProfile).mockRejectedValueOnce(new ApiClientError('missing', 404, { code: 'PROFILE_NOT_FOUND', message: 'missing' }))
    const user = userEvent.setup()
    render(<AccountPanel available session={{ user_id: 'u-1', access_token: 'access', refresh_token: 'refresh', expires_in: 900, token_version: 1 }} />)
    await user.type(screen.getByLabelText('出生日期'), '1984-12-07')
    await user.click(screen.getByRole('button', { name: '读取已存档案' }))
    expect(await screen.findByText('当前账户还没有保存出生档案，请填写后保存。')).toBeInTheDocument()
    expect(screen.getByLabelText('出生日期')).toHaveValue('1984-12-07')
  })
  it('保存期间锁定资料，避免保存结果对应旧输入', async () => {
    let finish!: (value: Awaited<ReturnType<typeof saveStoredProfile>>) => void
    save.mockImplementationOnce(() => new Promise(resolve => { finish = resolve }))
    const user = userEvent.setup()
    render(<AccountPanel available session={{ user_id: 'u-1', access_token: 'access', refresh_token: 'refresh', expires_in: 900, token_version: 1 }} />)
    await user.type(screen.getByLabelText('出生日期'), '1984-12-07')
    await user.type(screen.getByLabelText('出生时间'), '16:30')
    await user.selectOptions(screen.getByLabelText('性别'), 'male')
    await user.type(screen.getByLabelText('出生地'), '北京')
    await user.click(await screen.findByRole('button', { name: /北京 · CN/ }))
    await user.click(screen.getByRole('button', { name: '保存档案' }))
    expect(screen.getByLabelText('出生日期')).toBeDisabled()
    expect(screen.getByLabelText('出生地')).toBeDisabled()
    finish({ profile_status: 'VALID', stored: true, trace_id: 'trace-1' })
    expect(await screen.findByText('档案已由后端确认保存。')).toBeInTheDocument()
    expect(screen.getByLabelText('出生日期')).toBeEnabled()
  })
  it('返回账户页面时沿用当前内存会话，不要求重新登录', () => {
    render(<AccountPanel available session={{ user_id: 'u-1', access_token: 'access', refresh_token: 'refresh', expires_in: 900, token_version: 1 }} />)
    expect(screen.getByRole('heading', { name: '出生档案' })).toBeInTheDocument()
    expect(screen.queryByLabelText('邮箱')).not.toBeInTheDocument()
  })

  it('出生地选项来自后端地点资料', async () => {
    render(<AccountPanel available session={{ user_id: 'u-1', access_token: 'access', refresh_token: 'refresh', expires_in: 900, token_version: 1 }} />)
    await waitFor(() => expect(screen.getByLabelText('出生地')).toBeEnabled())
    await userEvent.type(screen.getByLabelText('出生地'), '北京')
    await userEvent.click(await screen.findByRole('button', { name: /北京 · CN/ }))
    expect(screen.getByLabelText('出生地')).toHaveValue('北京 · CN')
    await userEvent.type(screen.getByLabelText('出生地'), 'x')
    expect(screen.getByRole('button', { name: '保存档案' })).toBeDisabled()
  })

  it('档案请求的会话过期时清理本地会话并提示重新登录', async () => {
    vi.mocked(readStoredProfile).mockRejectedValueOnce(new ApiClientError('expired', 401, { code: 'INVALID_TOKEN', message: 'expired' }))
    const onSessionChange = vi.fn()
    render(<AccountPanel available session={{ user_id: 'u-1', access_token: 'access', refresh_token: 'refresh', expires_in: 900, token_version: 1 }} onSessionChange={onSessionChange} />)
    await userEvent.click(screen.getByRole('button', { name: '读取已存档案' }))
    expect(await screen.findByText('身份凭据已失效，请重新登录。')).toBeInTheDocument()
    expect(onSessionChange).toHaveBeenCalledWith(null)
    expect(screen.queryByRole('heading', { name: '出生档案' })).not.toBeInTheDocument()
  })
  it('认证服务未装配时不能发起配对登录，不会自动建号', () => {
    render(<AccountPanel available={false} />)
    expect(screen.getByRole('button', { name: '设备配对登录' })).toBeDisabled()
    expect(screen.queryByRole('button', { name: '明确建号' })).not.toBeInTheDocument()
    expect(login).not.toHaveBeenCalled()
  })

  it('邮箱验证码由用户主动请求，验证成功后只在内存保存会话', async () => {
    requestCode.mockResolvedValueOnce({ status: 'sent_if_available' })
    verifyCode.mockResolvedValueOnce({
      user_id: 'u-1', access_token: 'access', refresh_token: 'refresh',
      expires_in: 900, token_version: 1,
    })
    me.mockResolvedValueOnce({ user_id: 'u-1', is_new_user: false,
      has_birth_info: false, has_heluo_model: false, devices: [] })
    const onSessionChange = vi.fn()
    const user = userEvent.setup()
    render(<AccountPanel available onSessionChange={onSessionChange} />)
    expect(requestCode).not.toHaveBeenCalled()
    await user.type(screen.getByLabelText('邮箱'), 'user@example.com')
    await user.click(screen.getByRole('button', { name: '发送验证码' }))
    expect(await screen.findByText(/验证码已发送/)).toBeInTheDocument()
    expect(requestCode).toHaveBeenCalledWith('user@example.com')
    await user.type(screen.getByLabelText('邮箱验证码'), '123456')
    await user.click(screen.getByRole('button', { name: '验证并登录' }))
    expect(await screen.findByText('已登录账户')).toBeInTheDocument()
    expect(verifyCode).toHaveBeenCalledWith('user@example.com', '123456')
    expect(onSessionChange).toHaveBeenCalledTimes(1)
    expect(screen.queryByText('refresh')).not.toBeInTheDocument()
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
    const onProfileReady = vi.fn()
    render(<AccountPanel available onProfileReady={onProfileReady} />)
    await user.type(screen.getByLabelText('设备 ID'), 'dev-1')
    await user.type(screen.getByLabelText('配对码'), 'pair-1')
    await user.click(screen.getByRole('button', { name: '设备配对登录' }))
    expect(await screen.findByText('已登录账户')).toBeInTheDocument()
    await user.type(screen.getByLabelText('出生日期'), '1984-12-07')
    await user.type(screen.getByLabelText('出生时间'), '16:30')
    await user.selectOptions(screen.getByLabelText('性别'), 'male')
    await user.type(screen.getByLabelText('时区（可选）'), 'Asia/Shanghai')
    await user.type(screen.getByLabelText('出生地'), '北京')
    await user.click(await screen.findByRole('button', { name: /北京 · CN/ }))
    await user.type(screen.getByLabelText('当前城市（可选）'), 'Beijing')
    await user.click(screen.getByRole('button', { name: '保存档案' }))
    expect(await screen.findByText('档案已由后端确认保存。')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: '查看个人今日' })).toBeInTheDocument()
    await user.type(screen.getByLabelText('出生地'), 'x')
    expect(screen.queryByRole('button', { name: '查看个人今日' })).not.toBeInTheDocument()
    expect(save).toHaveBeenCalledTimes(1)
    expect(save.mock.calls[0][1]).toBe('access')
    expect(save.mock.calls[0][0].location).toBe('CN_BEIJING')
  })
})
