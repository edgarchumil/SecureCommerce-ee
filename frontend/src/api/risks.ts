import { apiClient } from './client'
import type { CatalogItem, Risk, RiskBand, RiskPageData, RiskPayload, Treatment } from '../types/risks'

export async function getRisks(search = '', level = '', page = 1): Promise<RiskPageData> {
  const { data } = await apiClient.get<RiskPageData>('/risks', { params: { search: search || undefined, level: level || undefined, page } })
  return data
}
export async function getRiskBands(): Promise<RiskBand[]> {
  const { data } = await apiClient.get<{ bands: RiskBand[] }>('/settings/risk-bands')
  return data.bands
}
export async function createRisk(payload: RiskPayload): Promise<Risk> {
  const { data } = await apiClient.post<Risk>('/risks', payload); return data
}
export async function getThreats(): Promise<CatalogItem[]> {
  const { data } = await apiClient.get<CatalogItem[]>('/threats'); return data
}
export async function getVulnerabilities(): Promise<CatalogItem[]> {
  const { data } = await apiClient.get<CatalogItem[]>('/vulnerabilities'); return data
}
export async function getTreatments(riskId: string): Promise<Treatment[]> {
  const { data } = await apiClient.get<Treatment[]>(`/risks/${riskId}/treatments`); return data
}
export async function addTreatment(riskId: string, action: string, progress: number): Promise<Treatment> {
  const { data } = await apiClient.post<Treatment>(`/risks/${riskId}/treatments`, { action, progress, responsible_user_id: null, target_date: null, notes: null }); return data
}
