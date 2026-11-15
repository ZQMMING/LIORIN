import { afterEach, describe, expect, it, vi } from 'vitest'
import { cleanup, render, screen } from '@testing-library/react'
import App from '../App'
import userEvent from '@testing-library/user-event'

vi.mock('../api/today', () => ({ fetchToday: vi.fn() }))
vi.mock('../components/hexagram/HetuLuoshuHero', () => ({ default: () => null }))
vi.mock('../animation/hero', () => ({
  playHeroAnimation: vi.fn(),
  HeroStage: { TODAY_REVEAL: 8 },
  BREATHING_CSS: '',
}))

import { fetchToday } from '../api/today'

const fetchMock = vi.mocked(fetchToday)

afterEach(() => {
  cleanup()
  vi.clearAllMocks()
  vi.unstubAllEnvs()
})

describe('App 默认游客态', () => {
  it('更多页面可进入使用说明和账户入口', async () => {
    fetchMock.mockRejectedValueOnce(new Error('offline'))
    const user = userEvent.setup()
    render(<App />)
    await user.click(screen.getByRole('button', { name: '更多' }))
    await user.click(screen.getByRole('button', { name: /使用说明/ }))
    expect(screen.getByText('THE GUIDE / 使用指南')).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: '更多' }))
    await user.click(screen.getByRole('button', { name: /账户与出生档案/ }))
    expect(screen.getByRole('heading', { name: '游客' })).toBeInTheDocument()
  })
  it('启动时请求真实 /v1/today；服务不可用时显示错误，不回退个人模拟卡', async () => {
    fetchMock.mockRejectedValueOnce(new Error('network unavailable'))
    render(<App />)
    expect(fetchMock).toHaveBeenCalledTimes(1)
    expect(await screen.findByRole('alert')).toBeInTheDocument()
    expect(screen.queryByText('MOCK ONLY · 示例数据')).not.toBeInTheDocument()
  })

  it('本机预览模式后端断开时展示明确空状态，不展示模拟卦象', async () => {
    vi.stubEnv('VITE_LIORIN_LOCAL_PREVIEW', '1')
    fetchMock.mockRejectedValueOnce(new Error('backend unavailable'))
    render(<App />)
    expect(await screen.findByRole('status', { name: '本机预览状态' })).toBeInTheDocument()
    expect(screen.getByText('页面已就绪，数据服务尚未连接。')).toBeInTheDocument()
    expect(screen.queryByText('MOCK ONLY · 示例数据')).not.toBeInTheDocument()
    await userEvent.click(screen.getByRole('button', { name: '输入资料 · 本机测试' }))
    expect(screen.getByRole('heading', { name: '引擎问题排查。' })).toBeInTheDocument()
    expect(screen.getByLabelText('出生日期')).toBeInTheDocument()
  })

  it('收到契约不完整的 200 响应时停在错误态，不进入渲染', async () => {
    fetchMock.mockResolvedValueOnce({ calendar: { daily_hexagram: {} } } as never)
    render(<App />)
    expect(await screen.findByRole('alert')).toBeInTheDocument()
    expect(screen.queryByText('MOCK ONLY · 示例数据')).not.toBeInTheDocument()
  })
})
