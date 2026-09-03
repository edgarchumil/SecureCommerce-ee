import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'

import { AppProviders } from './providers/AppProviders'
import './styles.css'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <AppProviders />
  </StrictMode>,
)

