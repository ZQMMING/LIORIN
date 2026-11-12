/**
 * ErrorState 组件行为测试 —— 三种错误类型 + retry 回调 + a11y 属性。
 * 依据 LIORIN_FRONTEND_SPEC_V2.md §4 错误五分类（此处组件覆盖 network/calculation/entitlement）。
 */
import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import ErrorState from '../components/feedback/ErrorState'

describe('ErrorState', () => {
  it('network 类型显示标题 + retry 按钮', () => {
    const onRetry = vi.fn()
    render(<ErrorState type="network" onRetry={onRetry} />)
    expect(screen.getByText('网络连接失败')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /重新加载/ })).toBeInTheDocument()
  })

  it('calculation 类型显示标题，不显示 message', () => {
    render(<ErrorState type="calculation" onRetry={vi.fn()} />)
    expect(screen.getByText('个人今日信息暂时无法计算')).toBeInTheDocument()
    expect(screen.queryByText('请升级至 Premium 以查看完整内容')).not.toBeInTheDocument()
  })

  it('entitlement 类型显示 Premium 文案，无 retry 按钮', () => {
    render(<ErrorState type="entitlement" />)
    expect(screen.getByText('此内容需要高级权限')).toBeInTheDocument()
    expect(screen.getByText('请升级至 Premium 以查看完整内容')).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /重新加载/ })).not.toBeInTheDocument()
  })

  it('点击 retry 触发 onRetry 回调', async () => {
    const onRetry = vi.fn()
    render(<ErrorState type="network" onRetry={onRetry} />)
    await userEvent.click(screen.getByRole('button', { name: /重新加载/ }))
    expect(onRetry).toHaveBeenCalledTimes(1)
  })

  it('携带 role=alert 与 aria-live=assertive', () => {
    const { container } = render(<ErrorState type="network" onRetry={vi.fn()} />)
    const el = container.querySelector('.error-state')
    expect(el).toHaveAttribute('role', 'alert')
    expect(el).toHaveAttribute('aria-live', 'assertive')
  })
})
