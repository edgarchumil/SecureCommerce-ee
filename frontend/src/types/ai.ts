export interface RecommendedAction { action: string; rationale: string; priority: 'alta' | 'media' | 'baja' }
export interface AIRecommendation {
  id: string; risk_id: string | null; kind: string; status: 'draft' | 'approved' | 'rejected'
  title: string; summary: string; actions: RecommendedAction[]; references: string[]
  provider: string; model: string; prompt_version: string; is_fallback: boolean
  input_tokens: number; output_tokens: number; estimated_cost_usd: number
  created_at: string; updated_at: string
}
