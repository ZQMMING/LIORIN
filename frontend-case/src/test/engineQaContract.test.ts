import { afterEach, describe, expect, it, vi } from 'vitest'
import { InvalidEngineQaResponse, runEngineQa } from '../api/engineQa'

vi.mock('../api/http', () => ({ apiRequest: vi.fn() }))
import { apiRequest } from '../api/http'
const request = vi.mocked(apiRequest)
const input = { birth_date: '1980-06-22', hour: 12, birth_minute: 30, gender: 'male' as const, theme: 'WORK', analysis_date: '2026-08-17', timezone: 'Asia/Shanghai', location: 'CN_BEIJING' }

afterEach(() => vi.resetAllMocks())

describe('测试结果接口边界', () => {
  it('拒绝缺少结果字段的成功响应', async () => {
    request.mockResolvedValueOnce({ canonical_id: 'CC-TEST' })
    await expect(runEngineQa(input)).rejects.toBeInstanceOf(InvalidEngineQaResponse)
  })
  it('拒绝无法安全展示的四柱', async () => {
    request.mockResolvedValueOnce({ canonical_id: 'CC-TEST', source: 'computed', warning: 'test', result_available: { heluo: false, yijing_structure: false }, observed_evidence_by_engine: {}, ziping_claim_count: 0, claims: [], bazi_pillars: { year: {}, month: '丙寅', day: '戊辰', hour: '庚午' } })
    await expect(runEngineQa(input)).rejects.toBeInstanceOf(InvalidEngineQaResponse)
  })
})
