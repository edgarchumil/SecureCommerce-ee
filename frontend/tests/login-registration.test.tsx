import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'
import { login } from '../src/api/auth'
import { LoginPage } from '../src/pages/LoginPage'

vi.mock('../src/api/auth', () => ({ login: vi.fn() }))
vi.mock('../src/features/auth/AuthContext', () => ({ useAuth: () => ({ authenticate: vi.fn() }) }))
vi.mock('../src/pages/RegisterPage', () => ({ RegisterPage: ({ onBack }: { onBack: () => void }) => <><p>Formulario de nueva empresa</p><button onClick={onBack}>Volver al selector</button></> }))

describe('registro desde el selector de empresas', () => {
  it.each(['org_admin', 'analyst', 'viewer'])('muestra el registro solamente para administrador: %s', async (role) => {
    vi.mocked(login).mockResolvedValue({ access_token: '', token_type: 'bearer', expires_in: 0, mfa_required: false, organization_selection_required: true, organizations: [{ id: '1', name: 'Empresa Demo', slug: 'demo', role_code: role }] })
    const user = userEvent.setup()
    render(<MemoryRouter><LoginPage /></MemoryRouter>)
    expect(screen.queryByRole('button', { name: 'Registrar una empresa' })).not.toBeInTheDocument()
    await user.type(screen.getByLabelText('Correo electrónico'), 'admin@example.test')
    await user.type(screen.getByLabelText('Contraseña'), 'Clave-Segura-2026!')
    await user.click(screen.getByRole('button', { name: 'Ingresar' }))
    expect(await screen.findByRole('status')).toHaveAccessibleName('Cargando SecureCommerce Advisor')
    expect(await screen.findByText('Seleccione la empresa', {}, { timeout: 3000 })).toBeInTheDocument()
    const button = screen.queryByRole('button', { name: 'Registrar una empresa' })
    expect(Boolean(button)).toBe(role === 'org_admin')
    if (button) {
      vi.mocked(login).mockResolvedValue({ access_token: 'verified-admin', token_type: 'bearer', expires_in: 900, mfa_required: false, organization_selection_required: false, organizations: [] })
      await user.click(button)
      expect(await screen.findByText('Formulario de nueva empresa')).toBeInTheDocument()
      await user.click(screen.getByRole('button', { name: 'Volver al selector' }))
      expect(await screen.findByText('Seleccione la empresa')).toBeInTheDocument()
    }
  })
})
