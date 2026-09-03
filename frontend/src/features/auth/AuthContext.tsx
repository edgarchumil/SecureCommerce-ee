import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from 'react'

import { logout as logoutRequest, refresh } from '../../api/auth'
import { setAccessToken } from '../../api/client'

interface AuthValue {
  token: string | null
  initializing: boolean
  authenticate: (token: string) => void
  signOut: () => Promise<void>
}

const AuthContext = createContext<AuthValue | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(null)
  const [initializing, setInitializing] = useState(true)

  const authenticate = (newToken: string) => {
    setAccessToken(newToken)
    setToken(newToken)
  }

  useEffect(() => {
    refresh()
      .then((result) => authenticate(result.access_token))
      .catch(() => setAccessToken(null))
      .finally(() => setInitializing(false))
  }, [])

  const signOut = async () => {
    try {
      await logoutRequest()
    } finally {
      setAccessToken(null)
      setToken(null)
    }
  }

  const value = useMemo(
    () => ({ token, initializing, authenticate, signOut }),
    [token, initializing],
  )
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

// El hook comparte el contexto React intencionalmente con su proveedor.
// eslint-disable-next-line react-refresh/only-export-components
export function useAuth() {
  const value = useContext(AuthContext)
  if (!value) throw new Error('useAuth debe utilizarse dentro de AuthProvider')
  return value
}
