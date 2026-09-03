import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'

import { getRecommendations } from '../src/api/ai'
import { getRisks } from '../src/api/risks'
import { RecommendationsPage } from '../src/pages/RecommendationsPage'

vi.mock('../src/api/ai', () => ({ getRecommendations: vi.fn(), generateRecommendation: vi.fn(), reviewRecommendation: vi.fn() }))
vi.mock('../src/api/risks', () => ({ getRisks: vi.fn() }))

function renderPage() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(<QueryClientProvider client={client}><MemoryRouter><RecommendationsPage /></MemoryRouter></QueryClientProvider>)
}

describe('recomendaciones asistidas', () => {
  it('marca el contenido y exige revisión humana', async () => {
    vi.mocked(getRisks).mockResolvedValue({ items: [], total: 0, page: 1, page_size: 20, pages: 0 })
    vi.mocked(getRecommendations).mockResolvedValue([{ id: '1', risk_id: 'r1', kind: 'treatment_plan', status: 'draft', title: 'Plan defensivo', summary: 'Resumen sujeto a revisión de una persona responsable.', actions: [{ action: 'Habilitar MFA', rationale: 'Reduce la exposición.', priority: 'alta' }], references: ['NIST CSF 2.0'], provider: 'local', model: 'deterministic-fallback', prompt_version: 'risk-advisor-v1', is_fallback: true, input_tokens: 0, output_tokens: 0, estimated_cost_usd: 0, created_at: '2026-01-01', updated_at: '2026-01-01' }])
    renderPage()
    expect(await screen.findByText('Plan defensivo')).toBeInTheDocument()
    expect(screen.getByText(/Contenido asistido · modo local/)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Aprobar/ })).toBeInTheDocument()
    expect(screen.getByText(/no certifican cumplimiento/i)).toBeInTheDocument()
  })
})
