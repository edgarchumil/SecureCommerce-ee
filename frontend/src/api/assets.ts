import { apiClient } from './client'
import type { AssetFormValues } from '../schemas/assets'
import type { Asset, AssetPage } from '../types/assets'

function payload(values: AssetFormValues) {
  const { tags_text, ...fields } = values
  return {
    ...fields,
    acquisition_date: fields.acquisition_date || null,
    ip_address: fields.ip_address || null,
    tags: tags_text?.split(',').map((tag) => tag.trim()).filter(Boolean) ?? [],
    dependency_ids: [],
  }
}

export async function getAssets(search = ''): Promise<AssetPage> {
  const { data } = await apiClient.get<AssetPage>('/assets', { params: { search: search || undefined } })
  return data
}

export async function getAsset(id: string): Promise<Asset> {
  const { data } = await apiClient.get<Asset>(`/assets/${id}`)
  return data
}

export async function createAsset(values: AssetFormValues): Promise<Asset> {
  const { data } = await apiClient.post<Asset>('/assets', payload(values))
  return data
}

export async function updateAsset(id: string, values: AssetFormValues): Promise<Asset> {
  const { data } = await apiClient.put<Asset>(`/assets/${id}`, payload(values))
  return data
}

export async function deleteAsset(id: string): Promise<void> {
  await apiClient.delete(`/assets/${id}`)
}

