import { render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'

import { AuthProvider } from '../src/features/auth/AuthContext'
import { ProtectedRoute } from '../src/features/auth/ProtectedRoute'
import { loginSchema, registerSchema } from '../src/schemas/auth'

vi.mock('../src/api/auth', () => ({
  refresh: vi.fn().mockRejectedValue(new Error('sin sesión')),
  logout: vi.fn(),
}))

describe('autenticación', () => {
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
})
