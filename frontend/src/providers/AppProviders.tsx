import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter } from 'react-router-dom'

import { AppRoutes } from '../routes/AppRoutes'
import { AuthProvider } from '../features/auth/AuthContext'

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: 1, staleTime: 30_000 } },
})

export function AppProviders() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AuthProvider><AppRoutes /></AuthProvider>
      </BrowserRouter>
    </QueryClientProvider>
  )
}
