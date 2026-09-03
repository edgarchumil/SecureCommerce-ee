export type AssetType = 'server' | 'computer' | 'mobile' | 'network' | 'application' | 'database' | 'information' | 'cloud_service' | 'critical_account' | 'supplier' | 'other'
export type AssetStatus = 'active' | 'inactive' | 'maintenance' | 'retired'
export type ExposureLevel = 'internal' | 'limited' | 'public'

export interface Asset {
  id: string
  organization_id: string
  name: string
  internal_code: string
  asset_type: AssetType
  description: string | null
  owner: string | null
  technical_owner: string | null
  location: string | null
  ip_address: string | null
  operating_system: string | null
  manufacturer: string | null
  model: string | null
  exposure_level: ExposureLevel
  status: AssetStatus
  acquisition_date: string | null
  confidentiality_criticality: number
  integrity_criticality: number
  availability_criticality: number
  overall_criticality: number
  tags: string[]
  notes: string | null
  dependency_ids: string[]
  created_at: string
  updated_at: string
}

export interface AssetPage { items: Asset[]; total: number; page: number; page_size: number; pages: number }

