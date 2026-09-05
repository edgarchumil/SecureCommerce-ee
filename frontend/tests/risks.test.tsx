import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'
import { getRisks } from '../src/api/risks'
import { RisksPage } from '../src/pages/RisksPage'

vi.mock('../src/api/assets', () => ({ getAssets: vi.fn().mockResolvedValue({ items: [] }) }))
vi.mock('../src/api/risks', () => ({
  getRisks: vi.fn(async (search = '', level = '', page = 1) => ({ items: [], total: search || level ? 1 : 120, pages: search || level ? 1 : 6, page, page_size: 20 })),
  getRiskBands: vi.fn().mockResolvedValue([
    { level: 'low', minimum: 1, maximum: 4 }, { level: 'medium', minimum: 5, maximum: 9 },
    { level: 'high', minimum: 10, maximum: 15 }, { level: 'critical', minimum: 16, maximum: 25 },
  ]),
  getThreats: vi.fn().mockResolvedValue([]), getVulnerabilities: vi.fn().mockResolvedValue([]),
  getTreatments: vi.fn(), addTreatment: vi.fn(), createRisk: vi.fn(),
}))

describe('riesgos multiempresa', () => {
  it('usa los umbrales de la empresa y permite paginar y reiniciar con filtros', async () => {
    const user = userEvent.setup()
    const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
    render(<QueryClientProvider client={client}><MemoryRouter><RisksPage /></MemoryRouter></QueryClientProvider>)
    expect(await screen.findByTitle('Probabilidad 4, impacto 4 · Crítico')).toHaveClass('bg-red-100')
    expect(await screen.findByText('120 riesgos · Página 1 de 6')).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: 'Siguiente' }))
    expect(await screen.findByText('120 riesgos · Página 2 de 6')).toBeInTheDocument()
    await user.type(screen.getByRole('textbox', { name: 'Buscar riesgos' }), 'A12')
    await waitFor(() => expect(getRisks).toHaveBeenLastCalledWith('A12', '', 1))
    await user.selectOptions(screen.getByRole('combobox', { name: 'Filtrar por nivel' }), 'critical')
    await waitFor(() => expect(getRisks).toHaveBeenLastCalledWith('A12', 'critical', 1))
  })
})
