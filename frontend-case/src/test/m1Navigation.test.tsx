import { afterEach, describe, expect, it, vi } from 'vitest'
import { act, cleanup, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import App from '../App'

vi.mock('../api/today', () => ({ fetchToday: vi.fn().mockRejectedValue(new Error('offline')) }))
vi.mock('../api/authAvailability', () => ({ checkAuthAvailability: vi.fn().mockResolvedValue('unavailable') }))

afterEach(() => { cleanup(); window.history.replaceState(null, '', '/') })

describe('page navigation', () => {
  it('opens a deep link, navigates and responds to browser history', async () => {
    window.history.replaceState(null, '', '/guide')
    const user = userEvent.setup()
    render(<App />)
    expect(screen.getByText('THE GUIDE / 使用指南')).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: '我的' }))
    expect(window.location.pathname).toBe('/me')
    expect(screen.getByText('ME / 我的')).toBeInTheDocument()
    act(() => { window.history.replaceState(null, '', '/guide'); window.dispatchEvent(new PopStateEvent('popstate')) })
    expect(screen.getByText('THE GUIDE / 使用指南')).toBeInTheDocument()
    expect(screen.getAllByRole('main')).toHaveLength(1)
  })

  it('shows a recoverable unknown route', async () => {
    window.history.replaceState(null, '', '/missing')
    const user = userEvent.setup()
    render(<App />)
    expect(screen.getByRole('heading', { name: '页面不存在' })).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: '返回今日' }))
    expect(window.location.pathname).toBe('/')
  })

  it('connects the profile CTA and disables an unavailable premium CTA', async () => {
    const user = userEvent.setup()
    render(<App />)
    await user.click(screen.getByRole('button', { name: 'No Profile' }))
    await user.click(screen.getByRole('button', { name: '完善资料' }))
    expect(window.location.pathname).toBe('/me')
    await user.click(screen.getByRole('button', { name: '今日' }))
    await user.click(screen.getByRole('button', { name: 'Valid' }))
    const unlock = screen.getByRole('button', { name: '解锁私享内容' })
    expect(unlock).toBeDisabled()
    expect(screen.getByText('私享内容暂未开放。')).toBeInTheDocument()
  })
})
