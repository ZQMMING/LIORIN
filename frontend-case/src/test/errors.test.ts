/**
 * 契约错误处理测试 —— 两套错误外壳归一化
 * 依据 API_VIEW_CONTRACT.md §2：后端存在 {"error":...} 与 {"detail":...} 两套外壳。
 */
import { describe, it, expect } from 'vitest'
import {
  normalizeApiError,
  isApiErrorBody,
  isAuthDetailBody,
} from '../contracts/errors'

describe('normalizeApiError — 形态 A（业务错误）', () => {
  it('归一化 INVALID_INPUT 错误', () => {
    const body = {
      error: {
        code: 'INVALID_INPUT',
        message: 'request fields present but invalid',
        request_id: 'RR-123',
        trace_id: 'TRACE-456',
        details: [{ loc: ['body', 'birth_time'], msg: 'Field required', type: 'missing' }],
      },
    }
    const e = normalizeApiError(body)
    expect(e.code).toBe('INVALID_INPUT')
    expect(e.message).toBe('request fields present but invalid')
    expect(e.requestId).toBe('RR-123')
    expect(e.traceId).toBe('TRACE-456')
    expect(e.details).toHaveLength(1)
  })

  it('识别 isApiErrorBody', () => {
    expect(isApiErrorBody({ error: { code: 'X', message: 'y' } })).toBe(true)
    expect(isApiErrorBody({ detail: { code: 'X', message: 'y' } })).toBe(false)
  })
})

describe('normalizeApiError — 形态 B（auth gateway 未初始化）', () => {
  it('归一化 AUTH_UNAVAILABLE 错误', () => {
    const body = { detail: { code: 'AUTH_UNAVAILABLE', message: 'gateway not initialised' } }
    const e = normalizeApiError(body)
    expect(e.code).toBe('AUTH_UNAVAILABLE')
    expect(e.message).toBe('gateway not initialised')
    expect(e.requestId).toBeUndefined()
  })

  it('识别 isAuthDetailBody', () => {
    expect(isAuthDetailBody({ detail: { code: 'X', message: 'y' } })).toBe(true)
    expect(isAuthDetailBody({ error: { code: 'X', message: 'y' } })).toBe(false)
  })
})

describe('normalizeApiError — 兜底', () => {
  it('无法识别时返回 UNKNOWN', () => {
    const e = normalizeApiError(null)
    expect(e.code).toBe('UNKNOWN')
  })
})
