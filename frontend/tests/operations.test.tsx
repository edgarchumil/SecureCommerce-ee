import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'

import { IncidentsPage } from '../src/pages/IncidentsPage'

vi.mock('../src/api/administration', () => ({
  getIncidents: vi.fn().mockResolvedValue([
    { id: '1', title: 'Correo sospechoso', description: 'Evento ficticio', severity: 'high', status: 'open', occurred_at: '2026-09-03T10:00:00Z', resolved_at: null },
  ]),
  createIncident: vi.fn(),
  updateIncident: vi.fn(),
}))

describe('operaciones de seguridad', () => {
  it('presenta incidentes y controles de seguimiento', async () => {
    const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
    render(<QueryClientProvider client={client}><MemoryRouter><IncidentsPage /></MemoryRouter></QueryClientProvider>)
    expect(await screen.findByText('Correo sospechoso')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Registrar incidente' })).toBeInTheDocument()
    expect(screen.getByRole('combobox', { name: 'Estado de Correo sospechoso' })).toHaveValue('open')
  })
})
