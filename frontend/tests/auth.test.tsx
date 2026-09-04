import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'

import { AuthProvider } from '../src/features/auth/AuthContext'
import { ProtectedRoute } from '../src/features/auth/ProtectedRoute'
import { PasswordInput } from '../src/components/PasswordInput'
import { loginSchema, normalizeOrganizationSlug, registerSchema } from '../src/schemas/auth'

vi.mock('../src/api/auth', () => ({
  refresh: vi.fn().mockRejectedValue(new Error('sin sesión')),
  logout: vi.fn(),
}))

describe('autenticación', () => {
  it('permite mostrar y ocultar una contraseña', async () => {
    const user = userEvent.setup()
    render(<PasswordInput aria-label="Contraseña" />)
    const input = screen.getByLabelText('Contraseña')

    expect(input).toHaveAttribute('type', 'password')
    await user.click(screen.getByRole('button', { name: 'Mostrar contraseña' }))
    expect(input).toHaveAttribute('type', 'text')
    await user.click(screen.getByRole('button', { name: 'Ocultar contraseña' }))
    expect(input).toHaveAttribute('type', 'password')
  })

  it('valida correo, contraseña y MFA', () => {
    expect(loginSchema.safeParse({ email: 'incorrecto', password: '' }).success).toBe(false)
    expect(
      loginSchema.safeParse({
        email: 'usuario@example.com',
        password: 'clave',
        mfa_code: '123456',
      }).success,
    ).toBe(true)
  })

  it('protege rutas sin sesión', async () => {
    render(
      <MemoryRouter initialEntries={['/panel']}>
        <AuthProvider>
          <Routes>
            <Route element={<ProtectedRoute />}>
              <Route path="/panel" element={<p>Contenido protegido</p>} />
            </Route>
            <Route path="/login" element={<p>Página de acceso</p>} />
          </Routes>
        </AuthProvider>
      </MemoryRouter>,
    )
    expect(await screen.findByText('Página de acceso')).toBeInTheDocument()
    expect(screen.queryByText('Contenido protegido')).not.toBeInTheDocument()
  })

  it('valida el registro de una organización', () => {
    expect(registerSchema.safeParse({ full_name: 'Ana López', email: 'ana@empresa.test', password: 'Clave-Segura-2026!', organization_name: 'Empresa Dos', organization_slug: 'empresa-dos', country: 'GT' }).success).toBe(true)
    expect(registerSchema.safeParse({ full_name: 'A', email: 'incorrecto', password: 'corta', organization_name: '', organization_slug: 'Empresa Dos', country: 'G' }).success).toBe(false)
  })

  it('convierte una URL de empresa en un identificador válido', () => {
    expect(normalizeOrganizationSlug('https://segurosgyt.com.gt')).toBe('segurosgyt-com-gt')
    expect(normalizeOrganizationSlug(' Mi Empresa ')).toBe('mi-empresa')
    const result = registerSchema.safeParse({ full_name: 'Ana López', email: 'ana@empresa.test', password: 'Clave-Segura-2026!', organization_name: 'Seguros GYT', organization_slug: 'https://segurosgyt.com.gt', country: 'GT' })
    expect(result.success && result.data.organization_slug).toBe('segurosgyt-com-gt')
  })
})
