import { afterEach, expect, it, vi } from 'vitest'
import { cleanup, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import DailyExplorerCalendar from '../pages/today/DailyExplorerCalendar'
import { apiRequest } from '../api/http'

vi.mock('../api/http', () => ({ apiRequest: vi.fn() }))

const request = vi.mocked(apiRequest)
const selection = { targetDate: '2026-02-17', displayTimezone: 'America/New_York' }
const pending = { status: 'unavailable', reason: 'field_admission_pending' }
const data = {
  requested_local_date: selection.targetDate, display_timezone: selection.displayTimezone, lunar_date: '正月 初一',
  source: { id: 'lunar_python', version: '1.4.8', registry_version: '1.0.0', date_basis: 'explicit_gregorian_date' },
  day_branch: { code: 'XU', name: '戌', checked_with: 'sxtwl', check_version: '2.0.7' },
  directions: pending, zodiac_connections: pending, time_windows: pending,
}

afterEach(() => { cleanup(); request.mockReset() })

it('shows admitted calendar facts and provenance in each supported locale', async () => {
  request.mockResolvedValueOnce(data)
  const user = userEvent.setup()
  render(<DailyExplorerCalendar selection={selection} />)
  expect(await screen.findByText('正月 初一')).toBeInTheDocument()
  expect(screen.getByText('Day branch')).toBeVisible()
  expect(screen.getByText('戌')).toBeVisible()
  expect(request).toHaveBeenCalledWith(
    '/v1/explorer/calendar?target_date=2026-02-17&display_timezone=America%2FNew_York',
    expect.objectContaining({ signal: expect.any(AbortSignal) }),
  )
  expect(screen.getAllByText(/source review pending/)).toHaveLength(3)
  await user.click(screen.getByText('Calendar source'))
  expect(screen.getByText(/lunar_python 1.4.8/)).toBeVisible()
  await user.selectOptions(screen.getByLabelText('Language'), 'zh-Hans')
  expect(screen.getByRole('heading', { name: '当日黄历' })).toBeVisible()
  await user.selectOptions(screen.getByLabelText('语言'), 'zh-Hant')
  expect(screen.getByRole('heading', { name: '當日黃曆' })).toBeVisible()
  expect(screen.getAllByText(/來源待審核/)).toHaveLength(3)
})

it('rejects mismatched dates and recovers after explicitly retrying', async () => {
  request.mockResolvedValueOnce({ ...data, requested_local_date: '2026-02-18' }).mockResolvedValueOnce(data)
  const user = userEvent.setup()
  render(<DailyExplorerCalendar selection={selection} />)
  expect(await screen.findByRole('alert')).toHaveTextContent('Calendar unavailable.')
  expect(screen.queryByText('正月 初一')).not.toBeInTheDocument()
  await user.click(screen.getByRole('button', { name: 'Retry calendar' }))
  expect(await screen.findByText('正月 初一')).toBeInTheDocument()
})

it('keeps the lunar date when the branch cross-check is unavailable', async () => {
  request.mockResolvedValueOnce({ ...data, day_branch: null })
  render(<DailyExplorerCalendar selection={selection} />)
  expect(await screen.findByText('Day branch unavailable')).toBeVisible()
  expect(screen.getByText('正月 初一')).toBeVisible()
  expect(screen.queryByText('戌')).not.toBeInTheDocument()
})
