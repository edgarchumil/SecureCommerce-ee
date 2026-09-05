import { act, render, screen } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { HomePage } from '../src/pages/HomePage'

function renderPage() {
  return render(<BrowserRouter><HomePage /></BrowserRouter>)
}

describe('HomePage', () => {
  beforeEach(() => vi.useFakeTimers())
  afterEach(() => vi.useRealTimers())
  it('muestra el logo y el nombre durante dos segundos', () => {
    renderPage()
    expect(screen.getByRole('status')).toHaveAccessibleName('Cargando SecureCommerce Advisor')
    expect(screen.getByText('SecureCommerce')).toBeInTheDocument()
    act(() => vi.advanceTimersByTime(1999))
    expect(screen.getByRole('status')).toBeInTheDocument()
    act(() => vi.advanceTimersByTime(1))
    expect(screen.queryByRole('status')).not.toBeInTheDocument()
  })
  it('presenta la propuesta de valor de la plataforma', () => {
    renderPage()
    act(() => vi.advanceTimersByTime(2000))
    expect(screen.getByRole('heading', { name: /proteja su empresa/i })).toBeInTheDocument()
    expect(screen.getByText('Evaluación NIST CSF 2.0')).toBeInTheDocument()
  })

  it('enlaza el acceso principal con el inicio de sesión', () => {
    renderPage()
    act(() => vi.advanceTimersByTime(2000))
    const links = screen.getAllByRole('link', { name: /iniciar sesión|acceder a la plataforma/i })
    expect(links.some((link) => link.getAttribute('href') === '/login')).toBe(true)
  })
})
