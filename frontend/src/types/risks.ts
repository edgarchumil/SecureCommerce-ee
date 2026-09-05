export type RiskLevel = 'low' | 'medium' | 'high' | 'critical'
export interface RiskBand { level: RiskLevel; minimum: number; maximum: number }
export type RiskStatus = 'identified' | 'analyzing' | 'in_treatment' | 'accepted' | 'closed'
export type TreatmentStrategy = 'avoid' | 'mitigate' | 'transfer' | 'accept'

export interface RiskPayload {
  code: string; title: string; description: string; asset_id: string
  threat_id: string | null; vulnerability_id: string | null
  probability: number; impact: number; existing_controls: string | null
  residual_probability: number; residual_impact: number
  treatment_strategy: TreatmentStrategy; responsible_user_id: string | null
  target_date: string | null; progress: number; status: RiskStatus
}
export interface Risk extends RiskPayload {
  id: string; organization_id: string; inherent_score: number; inherent_level: RiskLevel
  residual_score: number; residual_level: RiskLevel; created_at: string; updated_at: string
}
export interface RiskPageData { items: Risk[]; total: number; page: number; page_size: number; pages: number }
export interface CatalogItem { id: string; name: string; description: string; rating: number }
export interface Treatment { id: string; risk_id: string; action: string; responsible_user_id: string | null; target_date: string | null; progress: number; notes: string | null; created_at: string; updated_at: string }
