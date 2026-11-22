import { cleanup, render, screen } from '@testing-library/react'
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
