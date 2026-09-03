import { apiClient } from './client'
import type { DashboardData, DashboardFilters } from '../types/dashboard'

export async function getDashboard(filters: DashboardFilters): Promise<DashboardData> {
  const { data } = await apiClient.get<DashboardData>('/dashboard', { params: {
    date_from: filters.dateFrom || undefined,
    date_to: filters.dateTo || undefined,
    asset_type: filters.assetType || undefined,
  } })
  return data
}
