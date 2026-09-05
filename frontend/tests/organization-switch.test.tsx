import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { expect, it, vi } from 'vitest'
import { OrganizationsPage } from '../src/pages/OrganizationsPage'

vi.mock('../src/api/auth', () => ({
  getMyOrganizations: vi.fn().mockResolvedValue([{ id: 'tecno', name: 'TecnoMarket GT', slug: 'tecnomarket-gt', role_code: 'org_admin' }]),
  selectOrganization: vi.fn().mockResolvedValue({ access_token: 'selected-organization' }),
}))
vi.mock('../src/features/auth/AuthContext', () => ({ useAuth: () => ({ authenticate: vi.fn() }) }))
vi.mock('../src/pages/OrganizationPage', () => ({ Page: ({ children }: { children: React.ReactNode }) => <main>{children}</main> }))

it('descarta la caché de la empresa anterior al cambiar a TecnoMarket', async () => {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  client.setQueryData(['risk-bands'], [{ level: 'high', maximum: 16 }])
  client.setQueryData(['risks', '', '', 1], { items: ['previous-organization'] })
  render(<QueryClientProvider client={client}><MemoryRouter initialEntries={['/empresas']}><Routes>
    <Route path="/empresas" element={<OrganizationsPage />} /><Route path="/panel" element={<p>Empresa seleccionada</p>} />
  </Routes></MemoryRouter></QueryClientProvider>)
  await userEvent.click(await screen.findByRole('button', { name: /TecnoMarket GT/ }))
  await screen.findByText('Empresa seleccionada')
  await waitFor(() => expect(client.getQueryData(['risk-bands'])).toBeUndefined())
  expect(client.getQueryData(['risks', '', '', 1])).toBeUndefined()
})
