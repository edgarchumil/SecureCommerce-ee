export interface Metric { key: string; label: string; value: number; unit: string | null }
export interface ChartPoint { key: string; label: string; value: number }
export interface DashboardData {
  filters: { date_from: string | null; date_to: string | null; asset_type: string | null }
  kpis: Metric[]
  assets_by_type: ChartPoint[]
  risks_by_level: ChartPoint[]
  evaluations_by_status: ChartPoint[]
  risks_over_time: ChartPoint[]
}
export interface DashboardFilters { dateFrom: string; dateTo: string; assetType: string }
