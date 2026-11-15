import { afterEach, expect, it, vi } from 'vitest'
import { cleanup, render, screen } from '@testing-library/react'
import AppShell from '../components/shell/AppShell'

afterEach(cleanup)

it('切换页面时从新页面顶部开始', () => {
  const onPageChange = vi.fn()
  const { rerender } = render(<AppShell activePage="today" onPageChange={onPageChange}><p>今日内容</p></AppShell>)
  const main = screen.getByRole('main')
  main.scrollTop = 600
  rerender(<AppShell activePage="me" onPageChange={onPageChange}><p>账户内容</p></AppShell>)
  expect(main.scrollTop).toBe(0)
  expect(screen.getByText('账户内容')).toBeInTheDocument()
  main.scrollTop = 400
  rerender(<AppShell activePage="me" viewKey="details" onPageChange={onPageChange}><p>账户详情</p></AppShell>)
  expect(main.scrollTop).toBe(0)
})
