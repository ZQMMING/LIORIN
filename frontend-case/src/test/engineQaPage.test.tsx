import { afterEach, describe, expect, it, vi } from 'vitest'
import { cleanup, render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import EngineQaPage from '../pages/EngineQaPage'
import { ApiClientError } from '../api/http'

vi.mock('../api/engineQa', () => ({ runEngineQa: vi.fn(), InvalidEngineQaResponse: class extends Error {} }))
vi.mock('../api/locations', () => ({ fetchBirthLocations: vi.fn().mockResolvedValue([{ id: 'CN_BEIJING', name: '北京', country: 'CN', timezone: 'Asia/Shanghai' }]) }))
import { runEngineQa } from '../api/engineQa'
import { fetchBirthLocations } from '../api/locations'
const run = vi.mocked(runEngineQa)

afterEach(() => { cleanup(); vi.clearAllMocks() })

describe('本机引擎测试工作台', () => {
  it('城市列表不可用时不猜测地点，可重试加载', async () => {
    vi.mocked(fetchBirthLocations).mockRejectedValueOnce(new Error('offline'))
    const user = userEvent.setup()
    render(<EngineQaPage />)
    expect(await screen.findByText('城市列表暂不可用，无法确认出生地，请重试。')).toBeInTheDocument()
    expect(screen.getByLabelText('出生地')).toBeDisabled()
    await user.click(screen.getByRole('button', { name: '重试加载城市' }))
    await waitFor(() => expect(screen.getByLabelText('出生地')).toBeEnabled())
  })
  it('城市列表加载期间不提交，加载后可选择城市', async () => {
    let finish!: (items: Array<{ id: string; name: string; country: string; timezone: string }>) => void
    vi.mocked(fetchBirthLocations).mockImplementationOnce(() => new Promise(resolve => { finish = resolve }))
    const user = userEvent.setup()
    render(<EngineQaPage />)
    await user.click(screen.getByRole('button', { name: '载入测试命例（不自动提交）' }))
    expect(screen.getByLabelText('出生地')).toBeDisabled()
    expect(screen.getByRole('button', { name: '运行引擎测试' })).toBeDisabled()
    finish([{ id: 'CN_BEIJING', name: '北京', country: 'CN', timezone: 'Asia/Shanghai' }])
    expect(await screen.findByDisplayValue('北京 · CN')).toBeEnabled()
    expect(screen.getByRole('button', { name: '运行引擎测试' })).toBeEnabled()
  })
  it('出生地无法识别时说明如何修正', async () => {
    run.mockRejectedValueOnce(new ApiClientError('invalid', 400, { code: 'INVALID_INPUT', message: 'invalid', details: [{ field: 'location' }] }))
    const user = userEvent.setup()
    render(<EngineQaPage />)
    await user.click(screen.getByRole('button', { name: '载入测试命例（不自动提交）' }))
    await user.click(screen.getByRole('button', { name: '运行引擎测试' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('出生地无法识别，请重新搜索并选择城市。')
  })
  it('不会替用户预设性别、出生地点或出生分钟', () => {
    render(<EngineQaPage />)
    expect(screen.getByLabelText('性别')).toHaveValue('')
    expect(screen.getByLabelText('出生时间')).toHaveValue('')
    expect(screen.getByLabelText('出生地')).toHaveValue('')
    expect(screen.getByLabelText('时区')).toHaveValue('')
    const now = new Date()
    const today = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`
    expect(screen.getByLabelText('分析日期')).toHaveValue(today)
  })
  it('载入命例不自动请求，明确点击后显示有界摘要与 trace', async () => {
    run.mockResolvedValueOnce({
      analysis_date: '2026-08-17', canonical_id: 'CC-TEST', trace_id: 'TRACE-TEST',
      source: 'computed', validation_passed: false, validation_status: 'not_run',
      bazi_pillars: { year: '甲子', month: '丙寅', day: '戊辰', hour: '庚午' },
      observed_evidence_by_engine: { ZI_PING: 9 },
      result_available: { heluo: true, yijing_structure: true },
      ziping_claim_count: 4, heluo: { prenatal: '风天小畜', postnatal: '乾为天' },
      claims: [], claim_count: 0, warning: 'TEST ONLY',
    })
    const user = userEvent.setup()
    render(<EngineQaPage />)
    await user.click(screen.getByRole('button', { name: '载入测试命例（不自动提交）' }))
    expect(screen.getByLabelText('出生日期')).toHaveValue('1980-06-22')
    expect(run).not.toHaveBeenCalled()
    await user.click(screen.getByRole('button', { name: '运行引擎测试' }))
    expect(await screen.findByRole('status', { name: '引擎测试结果' })).toBeInTheDocument()
    expect(screen.getByText('风天小畜')).toBeInTheDocument()
    expect(screen.getByText('乾为天')).toBeInTheDocument()
    expect(screen.getByLabelText('八字四柱')).toHaveTextContent('甲子')
    expect(screen.getByLabelText('八字四柱')).toHaveTextContent('庚午')
    expect(screen.getByText(/TRACE-TEST/)).toBeInTheDocument()
    expect(screen.getByText(/未执行（本次仅计算）/)).toBeInTheDocument()
    expect(run).toHaveBeenCalledWith(expect.objectContaining({
      birth_date: '1980-06-22', hour: 12, birth_minute: 30, analysis_date: '2026-08-17',
      timezone: 'Asia/Shanghai', location: 'CN_BEIJING',
    }))
    await user.clear(screen.getByLabelText('出生时间'))
    expect(screen.queryByRole('status', { name: '引擎测试结果' })).not.toBeInTheDocument()
  })
  it('选择城市后采用城市资料中的时区', async () => {
    vi.mocked(fetchBirthLocations).mockResolvedValueOnce([{ id: 'CN_BEIJING', name: '北京', country: 'CN', timezone: 'Asia/Shanghai' }])
    const user = userEvent.setup()
    render(<EngineQaPage />)
    await waitFor(() => expect(screen.getByLabelText('出生地')).toBeEnabled())
    await user.type(screen.getByLabelText('出生地'), '北京')
    await user.click(await screen.findByRole('button', { name: /北京 · CN/ }))
    expect(screen.getByLabelText('时区')).toHaveValue('Asia/Shanghai')
    expect(screen.getByLabelText('出生地')).toHaveValue('北京 · CN')
  })
  it('切换示例或清空时同步重置正在编辑的城市', async () => {
    vi.mocked(fetchBirthLocations).mockResolvedValueOnce([{ id: 'CN_BEIJING', name: '北京', country: 'CN', timezone: 'Asia/Shanghai' }])
    const user = userEvent.setup()
    render(<EngineQaPage />)
    await user.type(screen.getByLabelText('出生地'), '北京')
    await user.click(screen.getByRole('button', { name: '载入测试命例（不自动提交）' }))
    expect(screen.getByLabelText('出生地')).toHaveValue('北京 · CN')
    await user.clear(screen.getByLabelText('出生地'))
    await user.type(screen.getByLabelText('出生地'), '北京')
    await user.click(screen.getByRole('button', { name: '清空输入与结果' }))
    expect(screen.getByLabelText('出生地')).toHaveValue('')
  })
})
