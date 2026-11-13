import { describe, expect, it } from 'vitest'
import { render, screen } from '@testing-library/react'
import MePage from '../pages/MePage'

describe('游客身份与权限边界', () => {
  it('不伪称已登录、免费订阅或已开放个人命盘', () => {
    render(<MePage />)
    expect(screen.getByRole('heading', { name: '游客' })).toBeInTheDocument()
    expect(screen.getByText('PUBLIC')).toBeInTheDocument()
    expect(screen.getByText('个人档案尚未开放')).toBeInTheDocument()
    expect(screen.getByText('个人命盘暂不可用')).toBeInTheDocument()
    expect(screen.queryByText('AUTHENTICATED')).not.toBeInTheDocument()
    expect(screen.queryByText('FREE')).not.toBeInTheDocument()
    expect(screen.queryByText('命盘查看')).not.toBeInTheDocument()
  })
})
