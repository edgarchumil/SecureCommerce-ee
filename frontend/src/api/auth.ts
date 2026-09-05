import { apiClient } from './client'
import type { LoginValues, RegisterValues } from '../schemas/auth'

export interface OrganizationOption { id: string; name: string; slug: string; role_code: string }

export interface TokenResponse {
  access_token: string
  token_type: 'bearer'
  expires_in: number
  mfa_required: boolean
  organization_selection_required: boolean
  organizations: OrganizationOption[]
}

export interface UserProfile {
  id: string
  email: string
  full_name: string
  is_active: boolean
  mfa_enabled: boolean
  is_superadmin?: boolean
  role_code?: string | null
  organization_id?: string | null
  organization_name?: string | null
}

export interface ActiveSession {
  id: string
  created_at: string
  expires_at: string
  revoked_at: string | null
  ip_address: string | null
  user_agent: string | null
}

export async function login(values: LoginValues): Promise<TokenResponse> {
  const { data } = await apiClient.post<TokenResponse>('/auth/login', { ...values, mfa_code: values.mfa_code || undefined })
  return data
}

export async function registerOrganization(values: RegisterValues): Promise<{ id: string }> {
  return (await apiClient.post<{ id: string }>('/auth/register', { ...values, country: values.country.toUpperCase() })).data
}
export async function getMyOrganizations(): Promise<OrganizationOption[]> { return (await apiClient.get<OrganizationOption[]>('/auth/organizations')).data }
export async function selectOrganization(organization_id: string): Promise<TokenResponse> { return (await apiClient.post<TokenResponse>('/auth/select-organization', { organization_id })).data }

export async function refresh(): Promise<TokenResponse> {
  const { data } = await apiClient.post<TokenResponse>('/auth/refresh', {})
  return data
}

export async function logout(): Promise<void> {
  await apiClient.post('/auth/logout')
}

export async function getProfile(): Promise<UserProfile> {
  const { data } = await apiClient.get<UserProfile>('/auth/me')
  return data
}

export async function getSessions(): Promise<ActiveSession[]> {
  const { data } = await apiClient.get<ActiveSession[]>('/sessions')
  return data
}

export async function revokeSession(sessionId: string): Promise<void> {
  await apiClient.delete(`/sessions/${sessionId}`)
}

export async function setupMfa(): Promise<{ secret: string; provisioning_uri: string }> {
  return (await apiClient.post('/auth/mfa/setup')).data
}

export async function verifyMfa(code: string): Promise<void> {
  await apiClient.post('/auth/mfa/verify', { code })
}
