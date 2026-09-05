import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'
import { getProfile } from '../src/api/auth'
import { AdminRoute } from '../src/features/auth/AdminRoute'
import { AppShell } from '../src/components/AppShell'

vi.mock('../src/api/auth', () => ({ getProfile: vi.fn() }))
vi.mock('../src/features/auth/AuthContext', () => ({ useAuth: () => ({ token: 'session', signOut: vi.fn() }) }))

describe('registro exclusivo para administradores', () => {
  it.each(['org_admin', 'superadmin', 'analyst', 'viewer'])('protege el formulario y el menú para %s', async (role) => {
    vi.mocked(getProfile).mockResolvedValue({ id: '1', email: 'user@example.test', full_name: 'Usuario', is_active: true, mfa_enabled: false, role_code: role })
    render(<QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}>
      <MemoryRouter initialEntries={['/registro']}><Routes>
        <Route element={<AppShell />}>
          <Route element={<AdminRoute />}><Route path="/registro" element={<p>Formulario de registro</p>} /></Route>
          <Route path="/panel" element={<p>Panel ejecutivo de prueba</p>} />
        </Route>
      </Routes></MemoryRouter>
    </QueryClientProvider>)
    const allowed = ['org_admin', 'superadmin'].includes(role)
    expect(await screen.findByText(allowed ? 'Formulario de registro' : 'Panel ejecutivo de prueba')).toBeInTheDocument()
    expect(Boolean(screen.queryByRole('link', { name: 'Registrar una empresa' }))).toBe(false)
  })
})
