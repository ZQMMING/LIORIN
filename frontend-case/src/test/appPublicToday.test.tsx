import { afterEach, describe, expect, it, vi } from 'vitest'
import { cleanup, render, screen } from '@testing-library/react'
import App from '../App'

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
})

describe('App 默认游客态', () => {
  it('启动时请求真实 /v1/today；服务不可用时显示错误，不回退个人模拟卡', async () => {
    fetchMock.mockRejectedValueOnce(new Error('network unavailable'))
    render(<App />)
    expect(fetchMock).toHaveBeenCalledTimes(1)
    expect(await screen.findByRole('alert')).toBeInTheDocument()
    expect(screen.queryByText('MOCK ONLY · 示例数据')).not.toBeInTheDocument()
  })

  it('收到契约不完整的 200 响应时停在错误态，不进入渲染', async () => {
    fetchMock.mockResolvedValueOnce({ calendar: { daily_hexagram: {} } } as never)
    render(<App />)
    expect(await screen.findByRole('alert')).toBeInTheDocument()
    expect(screen.queryByText('MOCK ONLY · 示例数据')).not.toBeInTheDocument()
  })
})
