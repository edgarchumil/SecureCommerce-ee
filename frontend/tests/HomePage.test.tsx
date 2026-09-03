import { render, screen } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { describe, expect, it } from 'vitest'

import { HomePage } from '../src/pages/HomePage'

function renderPage() {
  return render(<BrowserRouter><HomePage /></BrowserRouter>)
}

describe('HomePage', () => {
  it('presenta la propuesta de valor de la plataforma', () => {
    renderPage()
    expect(screen.getByRole('heading', { name: /proteja su empresa/i })).toBeInTheDocument()
    expect(screen.getByText('Evaluación NIST CSF 2.0')).toBeInTheDocument()
  })

  it('enlaza el acceso principal con el inicio de sesión', () => {
    renderPage()
    const links = screen.getAllByRole('link', { name: /iniciar sesión|acceder a la plataforma/i })
    expect(links.some((link) => link.getAttribute('href') === '/login')).toBe(true)
  })
})
