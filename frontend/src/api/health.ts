import { apiClient } from './client'

export interface HealthResponse {
  status: 'ok'
}

export async function getHealth(): Promise<HealthResponse> {
  const response = await apiClient.get<HealthResponse>('/health/live')
  return response.data
}

