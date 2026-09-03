import { apiClient } from './client'
import type { AIRecommendation, RecommendedAction } from '../types/ai'

export async function getRecommendations(): Promise<AIRecommendation[]> {
  const { data } = await apiClient.get<AIRecommendation[]>('/ai/recommendations'); return data
}
export async function generateRecommendation(riskId: string): Promise<AIRecommendation> {
  const { data } = await apiClient.post<AIRecommendation>('/ai/recommendations/generate', { risk_id: riskId, kind: 'treatment_plan' }); return data
}
export async function reviewRecommendation(id: string, status: AIRecommendation['status'], title: string, summary: string, actions: RecommendedAction[]): Promise<AIRecommendation> {
  const { data } = await apiClient.patch<AIRecommendation>(`/ai/recommendations/${id}`, { status, title, summary, actions }); return data
}
