import { afterEach, describe, expect, it, vi } from 'vitest'
import { cleanup, render, screen } from '@testing-library/react'
import { ApiClientError } from '../api/http'
import { checkAuthAvailability } from '../api/authAvailability'
import MePage from '../pages/MePage'

vi.mock('../api/http', async (importOriginal) => {
  const original = await importOriginal<typeof import('../api/http')>()
  return { ...original, apiRequest: vi.fn() }
})

import { apiRequest } from '../api/http'
const request = vi.mocked(apiRequest)

afterEach(() => { cleanup(); vi.resetAllMocks() })

describe('认证网关只读能力探测', () => {
  it('503 AUTH_UNAVAILABLE => 未装配，页面仍为游客', async () => {
    request.mockRejectedValueOnce(new ApiClientError('unavailable', 503, { code: 'AUTH_UNAVAILABLE', message: 'gateway not initialised' }))
    render(<MePage />)
    expect(await screen.findByText('认证服务尚未装配，当前无法建档或登录。')).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: '游客' })).toBeInTheDocument()
    expect(request).toHaveBeenCalledWith('/v1/auth/me')
    expect(request).toHaveBeenCalledTimes(1)
  })

  it('401 => 网关已装配但无令牌，不伪称已登录', async () => {
    request.mockRejectedValueOnce(new ApiClientError('unauthorized', 401, { code: 'INVALID_TOKEN', message: 'Missing authorization' }))
    render(<MePage />)
    expect(await screen.findByText('认证服务可用；当前仍是游客。登录入口尚未接入。')).toBeInTheDocument()
    expect(screen.queryByText('AUTHENTICATED')).not.toBeInTheDocument()
  })

  it('网络失败 => 不推断网关可用性', async () => {
    request.mockRejectedValueOnce(new TypeError('Failed to fetch'))
    expect(await checkAuthAvailability()).toBe('offline')
  })
})
