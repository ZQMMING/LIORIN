import { cleanup, render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, expect, it, vi } from 'vitest'
import { ApiClientError, apiRequest } from '../api/http'
import PersonalDnaPage from '../pages/PersonalDnaPage'

vi.mock('../api/http', async original => ({
  ...await original<typeof import('../api/http')>(),
  apiRequest: vi.fn(),
}))

const load = vi.mocked(apiRequest)
const handlers = { onAccount: vi.fn(), onSessionExpired: vi.fn() }

afterEach(() => { cleanup(); vi.clearAllMocks() })

it('does not request a private chart until signed in', () => {
  render(<PersonalDnaPage token={null} {...handlers} />)
  expect(screen.getByText('Sign in to view your Personal DNA.')).toBeVisible()
  expect(load).not.toHaveBeenCalled()
})

it('shows the birth-time limitation and takes the user to their profile', async () => {
  const user = userEvent.setup()
  load.mockRejectedValueOnce(new ApiClientError('incomplete', 422, {
    code: 'INCOMPLETE_BIRTH_TIME', message: 'Birth minute required.',
  } as ConstructorParameters<typeof ApiClientError>[2]))
  render(<PersonalDnaPage token="preview" {...handlers} />)
  expect(await screen.findByText('A complete, unambiguous birth time is required.')).toBeVisible()
  await user.click(screen.getByRole('button', { name: 'Open birth profile' }))
  expect(handlers.onAccount).toHaveBeenCalledOnce()
})

it('counts the eight visible positions and shows the Na Yin source', async () => {
  const user = userEvent.setup()
  load.mockResolvedValueOnce({
    birth_year_nayin: '海中金', day_master: '乙', day_master_element: 'WOOD',
    zodiac_status: 'pending_year_boundary_review', nayin_evidence_id: 'E-SMTH-003-001',
    pillars: [
      { position: 'year', name: '甲子', stem_element: 'WOOD', branch_element: 'WATER' },
      { position: 'month', name: '丙子', stem_element: 'FIRE', branch_element: 'WATER' },
      { position: 'day', name: '乙亥', stem_element: 'WOOD', branch_element: 'WATER' },
      { position: 'hour', name: '甲申', stem_element: 'WOOD', branch_element: 'METAL' },
    ],
    source: { chain: 'TimeResolver → CalculationContext → BaziAdapter', engine_version: 'bazi',
      calculation_version: 'calc', package_version: '1.1.1', calendar_version: '2.0.7', birth_timezone: 'Asia/Shanghai' },
  })
  render(<PersonalDnaPage token="preview" {...handlers} />)
  const table = await screen.findByRole('table', { name: 'Five-element structure' })
  const rowValues = (name: RegExp) => within(within(table).getByRole('row', { name }))
    .getAllByRole('cell').map(cell => cell.textContent)
  expect(rowValues(/Wood/)).toEqual(['3', '0', '3'])
  expect(rowValues(/Water/)).toEqual(['0', '3', '3'])
  expect(rowValues(/Earth/)).toEqual(['0', '0', '0'])
  await user.click(screen.getByText('Calculation source'))
  expect(screen.getByText(/E-SMTH-003-001/)).toBeVisible()
})
