import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { getProfile } from '../src/api/auth'
import { getDashboard } from '../src/api/dashboard'
import { PanelPage } from '../src/pages/PanelPage'

vi.mock('../src/api/auth', () => ({ getProfile: vi.fn() }))
vi.mock('../src/api/dashboard', () => ({ getDashboard: vi.fn() }))
vi.mock('../src/features/auth/AuthContext', () => ({ useAuth: () => ({ signOut: vi.fn() }) }))
vi.mock('recharts', () => ({
  ResponsiveContainer: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  BarChart: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  LineChart: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  PieChart: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  Bar: () => null, Line: () => null, Pie: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  Cell: () => null, CartesianGrid: () => null, Tooltip: () => null, XAxis: () => null, YAxis: () => null,
}))

function renderPage() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(<QueryClientProvider client={client}><MemoryRouter><PanelPage /></MemoryRouter></QueryClientProvider>)
}

describe('dashboard ejecutivo', () => {
  beforeEach(() => {
    vi.mocked(getProfile).mockResolvedValue({ id: '1', email: 'ana@example.com', full_name: 'Ana', is_active: true, mfa_enabled: false })
    vi.mocked(getDashboard).mockReset()
  })

  it('presenta KPIs, gráficas con alternativa textual y filtros', async () => {
    vi.mocked(getDashboard).mockResolvedValue({
      filters: { date_from: null, date_to: null, asset_type: null },
      kpis: [{ key: 'assets', label: 'Activos', value: 7, unit: null }, { key: 'maturity', label: 'Madurez NIST', value: 50, unit: '%' }, { key: 'risks', label: 'Riesgos abiertos', value: 2, unit: null }, { key: 'priority_risks', label: 'Riesgos prioritarios', value: 1, unit: null }],
      assets_by_type: [{ key: 'server', label: 'Servidor', value: 2 }], risks_by_level: [], evaluations_by_status: [], risks_over_time: [],
    })
    renderPage()
    expect(await screen.findByText('7')).toBeInTheDocument()
    expect(screen.getByRole('img', { name: /Activos por tipo: Servidor, 2/ })).toBeInTheDocument()
    expect(screen.getByRole('form', { name: 'Filtros del panel' })).toBeInTheDocument()
    expect(screen.getAllByText('Sin datos para los filtros seleccionados.')).toHaveLength(3)
  })

  it('muestra un estado de error accesible', async () => {
    vi.mocked(getDashboard).mockRejectedValue(new Error('fallo'))
    renderPage()
    expect(await screen.findByRole('alert')).toHaveTextContent('No fue posible cargar')
  })
})
