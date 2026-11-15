import { afterEach, expect, it } from 'vitest'
import { cleanup, render, screen } from '@testing-library/react'
import Header from '../components/shell/Header'

afterEach(cleanup)

it('未提供时区时不显示未经确认的时区', () => {
  render(<Header />)
  expect(screen.queryByText('GMT+8')).not.toBeInTheDocument()
})
