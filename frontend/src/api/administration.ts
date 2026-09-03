import { apiClient } from './client'

export interface Organization { id: string; name: string; slug: string; sector: string | null; size: string | null; country: string }
export interface Member { id: string; user_id: string; email: string; full_name: string; role_code: string; is_active: boolean }
export interface AuditEntry { id: string; action: string; resource_type: string; resource_id: string | null; result: string; correlation_id: string | null; created_at: string }
export interface Incident { id: string; title: string; description: string; severity: string; status: string; occurred_at: string; resolved_at: string | null }
export interface PlatformOrganization extends Organization { is_active: boolean; member_count: number }

export const getOrganization = async () => (await apiClient.get<Organization>('/organizations/current')).data
export const updateOrganization = async (payload: Partial<Organization>) => (await apiClient.patch<Organization>('/organizations/current', payload)).data
export const getMembers = async () => (await apiClient.get<Member[]>('/users')).data
export const inviteMember = async (payload: { email: string; full_name: string; role_code: string }) => (await apiClient.post<Member>('/memberships/invite', payload)).data
export const updateMemberRole = async (id: string, role_code: string) => (await apiClient.patch<Member>(`/memberships/${id}/role`, { role_code })).data
export const getAudit = async () => (await apiClient.get<AuditEntry[]>('/audit-logs')).data
export const getIncidents = async () => (await apiClient.get<Incident[]>('/incidents')).data
export const createIncident = async (payload: { title: string; description: string; severity: string; occurred_at: string }) => (await apiClient.post<Incident>('/incidents', payload)).data
export const updateIncident = async (id: string, status: string) => (await apiClient.patch<Incident>(`/incidents/${id}`, { status })).data
export const requestPasswordReset = async (email: string) => (await apiClient.post<{ message: string }>('/auth/password-reset/request', { email })).data
export const changePassword = async (current_password: string, new_password: string) => { await apiClient.post('/auth/change-password', { current_password, new_password }) }
export const getPlatformOrganizations = async () => (await apiClient.get<PlatformOrganization[]>('/platform/organizations')).data
export const updatePlatformOrganization = async (id: string, is_active: boolean) => (await apiClient.patch<PlatformOrganization>(`/platform/organizations/${id}`, { is_active })).data
