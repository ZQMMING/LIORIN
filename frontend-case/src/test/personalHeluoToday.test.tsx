import { afterEach, describe, expect, it, vi } from 'vitest'
import { act, cleanup, render, screen } from '@testing-library/react'
import RealPersonalHeluoToday from '../pages/today/RealPersonalHeluoToday'
import { ApiClientError } from '../api/http'
import userEvent from '@testing-library/user-event'

vi.mock('../api/heluoToday', () => ({ fetchPersonalHeluoToday: vi.fn() }))
import { fetchPersonalHeluoToday } from '../api/heluoToday'
const fetchMock = vi.mocked(fetchPersonalHeluoToday)

afterEach(() => { cleanup(); vi.resetAllMocks() })

describe('个人河洛五日一爻', () => {
  it('旧档案出生地有歧义时引导用户重新确认', async () => {
    const onProfileRequired = vi.fn()
    fetchMock.mockRejectedValueOnce(new ApiClientError('ambiguous', 422, { code: 'PROFILE_LOCATION_AMBIGUOUS', message: 'ambiguous' }))
    render(<RealPersonalHeluoToday token="access" onProfileRequired={onProfileRequired} />)
    await userEvent.click(await screen.findByRole('button', { name: '确认出生地' }))
    expect(onProfileRequired).toHaveBeenCalledOnce()
    expect(screen.queryByRole('img')).not.toBeInTheDocument()
  })
  it('返回日期不属于对应时间段时不展示结果', async () => {
    fetchMock.mockResolvedValueOnce({ date: '2026-11-18', hexagram: '火水未济', upper: '离', lower: '坎', lines: [1, -1, 1, -1, 1, -1], active_yao_index: 2, period_start: '2026-11-10', period_end: '2026-11-14', period_days: 5, source: 'heluo_timeline_liuri', trace_id: 'TRACE-1' })
    render(<RealPersonalHeluoToday token="access" />)
    expect(await screen.findByRole('alert')).toBeInTheDocument()
    expect(screen.queryByRole('heading', { name: '火水未济' })).not.toBeInTheDocument()
  })
  it('后端未提供上下卦时明确显示缺失', async () => {
    fetchMock.mockResolvedValueOnce({ date: '2026-11-12', hexagram: '火水未济', upper: null, lower: null, lines: [1, -1, 1, -1, 1, -1], active_yao_index: 2, period_start: '2026-11-10', period_end: '2026-11-14', period_days: 5, source: 'heluo_timeline_liuri', trace_id: 'TRACE-1' })
    render(<RealPersonalHeluoToday token="access" />)
    expect(await screen.findByText(/上卦 未提供 · 下卦 未提供/)).toBeInTheDocument()
  })
  it('切换账户后忽略旧请求的过期错误', async () => {
    let rejectOld!: (reason: Error) => void
    fetchMock.mockImplementationOnce(() => new Promise((_, reject) => { rejectOld = reject }))
    fetchMock.mockResolvedValueOnce({ date: '2026-11-12', hexagram: '火水未济', upper: '离', lower: '坎', lines: [1, -1, 1, -1, 1, -1], active_yao_index: 2, period_start: '2026-11-10', period_end: '2026-11-14', period_days: 5, source: 'heluo_timeline_liuri', trace_id: 'TRACE-1' })
    const onSessionExpired = vi.fn()
    const { rerender } = render(<RealPersonalHeluoToday token="old" onSessionExpired={onSessionExpired} />)
    rerender(<RealPersonalHeluoToday token="new" onSessionExpired={onSessionExpired} />)
    expect(await screen.findByRole('heading', { name: '火水未济' })).toBeInTheDocument()
    await act(async () => { rejectOld(new ApiClientError('expired', 401, { code: 'INVALID_TOKEN', message: 'expired' })) })
    expect(onSessionExpired).not.toHaveBeenCalled()
    expect(screen.getByRole('heading', { name: '火水未济' })).toBeInTheDocument()
  })
  it('尚无档案时提示填写资料并提供入口', async () => {
    const onProfileRequired = vi.fn()
    fetchMock.mockRejectedValueOnce(new ApiClientError('missing', 404, { code: 'PROFILE_NOT_FOUND', message: 'profile not found' }))
    render(<RealPersonalHeluoToday token="access" onProfileRequired={onProfileRequired} />)
    await userEvent.click(await screen.findByRole('button', { name: '填写出生资料' }))
    expect(onProfileRequired).toHaveBeenCalledOnce()
  })
  it('只展示后端给定的日期段与值日爻', async () => {
    fetchMock.mockResolvedValueOnce({
      date: '2026-11-12', hexagram: '火水未济', upper: '离', lower: '坎',
      lines: [1, -1, 1, -1, 1, -1], active_yao_index: 2,
      period_start: '2026-11-10', period_end: '2026-11-14', period_days: 5,
      source: 'heluo_timeline_liuri', trace_id: 'TRACE-1',
    })
    render(<RealPersonalHeluoToday token="access" />)
    expect(await screen.findByRole('heading', { name: '火水未济' })).toBeInTheDocument()
    expect(screen.getByText(/每爻管五日/)).toBeInTheDocument()
    expect(screen.getByText(/第 3 爻/)).toBeInTheDocument()
    expect(screen.getByRole('img', { name: '火水未济，当前第 3 爻' })).toBeInTheDocument()
    expect(document.querySelector('[data-yao="3"]')).toHaveClass('is-active')
    expect(fetchMock).toHaveBeenCalledWith('access')
  })

  it('爻值不是阴阳二值时拒绝展示结果', async () => {
    fetchMock.mockResolvedValueOnce({ date: '2026-11-12', hexagram: '火水未济', upper: '离', lower: '坎', lines: [1, 0, 9, 0, 1, 0], active_yao_index: 2, period_start: '2026-11-10', period_end: '2026-11-14', period_days: 5, source: 'heluo_timeline_liuri', trace_id: 'TRACE-1' })
    render(<RealPersonalHeluoToday token="access" />)
    expect(await screen.findByRole('alert')).toBeInTheDocument()
    expect(screen.queryByRole('img', { name: /火水未济/ })).not.toBeInTheDocument()
  })

  it('401 时通知上层清理会话，不展示公共卦', async () => {
    const onSessionExpired = vi.fn()
    fetchMock.mockRejectedValueOnce(new ApiClientError('expired', 401, { code: 'INVALID_TOKEN', message: 'expired' }))
    render(<RealPersonalHeluoToday token="access" onSessionExpired={onSessionExpired} />)
    expect(await screen.findByRole('alert')).toBeInTheDocument()
    expect(onSessionExpired).toHaveBeenCalledTimes(1)
    expect(screen.queryByText('火水未济')).not.toBeInTheDocument()
  })

  it('无唯一段或后端报错时停在计算错误，不回退公共卦', async () => {
    fetchMock.mockRejectedValueOnce(new Error('HELUO_DAY_UNAVAILABLE'))
    render(<RealPersonalHeluoToday token="access" />)
    expect(await screen.findByRole('alert')).toBeInTheDocument()
    expect(screen.queryByText('火水未济')).not.toBeInTheDocument()
  })
})
