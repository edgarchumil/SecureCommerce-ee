import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { expect, it, vi } from 'vitest'
import { getProfile } from '../src/api/auth'
import { ReportsPage } from '../src/pages/ReportsPage'

vi.mock('../src/features/auth/AuthContext', () => ({ useAuth: () => ({ token: 'test' }) }))
vi.mock('../src/api/auth', () => ({ getProfile: vi.fn() }))
vi.mock('../src/api/reports', () => ({ getReports: vi.fn().mockResolvedValue([]), createReport: vi.fn(), downloadReport: vi.fn() }))

it.each(['org_admin', 'analyst', 'viewer'])('muestra el alcance y respeta el rol %s', async (role) => {
  vi.mocked(getProfile).mockResolvedValue({ id: '1', full_name: 'Usuario', email: 'u@example.test', role_code: role, organization_name: 'Empresa actual', is_active: true, mfa_enabled: false })
  render(<QueryClientProvider client={new QueryClient()}><MemoryRouter><ReportsPage /></MemoryRouter></QueryClientProvider>)
  expect(await screen.findByText('Empresa actual')).toBeInTheDocument()
  expect(await screen.findByText('Todavía no hay informes')).toBeInTheDocument()
  expect(Boolean(screen.queryByRole('button', { name: 'Generar PDF' }))).toBe(role !== 'viewer')
  if (role !== 'viewer') expect(screen.getByLabelText(/Alcance declarado/)).toHaveValue('Activos, riesgos, controles e incidentes registrados para la empresa seleccionada.')
})
