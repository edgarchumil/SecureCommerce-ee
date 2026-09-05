import axe from 'axe-core'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { HomePage } from '../src/pages/HomePage'
import { LoginPage } from '../src/pages/LoginPage'
import { AuthProvider } from '../src/features/auth/AuthContext'

vi.mock('../src/api/health', () => ({
  getHealth: vi.fn().mockResolvedValue({ status: 'ok', services: {} }),
}))
vi.mock('../src/api/auth', () => ({
  refresh: vi.fn().mockRejectedValue(new Error('sin sesión')),
  logout: vi.fn(),
  login: vi.fn(),
}))

afterEach(() => vi.clearAllMocks())

async function expectNoViolations(container: HTMLElement) {
  const results = await axe.run(container, { rules: { 'color-contrast': { enabled: false } } })
  expect(results.violations).toEqual([])
}

describe('accesibilidad WCAG automatizada', () => {
  it('no detecta infracciones en la portada', async () => {
    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
    const { container } = render(
      <MemoryRouter><QueryClientProvider client={queryClient}>
        <HomePage />
      </QueryClientProvider></MemoryRouter>,
    )
    await screen.findByRole('heading', { name: /proteja su empresa/i }, { timeout: 3000 })
    await expectNoViolations(container)
  })

  it('no detecta infracciones en el acceso', async () => {
    const { container } = render(
      <MemoryRouter>
        <AuthProvider><LoginPage /></AuthProvider>
      </MemoryRouter>,
    )
    await screen.findByRole('button', { name: 'Ingresar' })
    await expectNoViolations(container)
  })
})
