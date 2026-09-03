import { apiClient } from './client'
import type { ReportItem } from '../types/reports'

export async function getReports(): Promise<ReportItem[]> { const { data } = await apiClient.get<ReportItem[]>('/reports'); return data }
export async function createReport(report_type: ReportItem['report_type'], title: string, scope: string): Promise<ReportItem> { const { data } = await apiClient.post<ReportItem>('/reports', { report_type, title, scope }); return data }
export async function downloadReport(item: ReportItem): Promise<void> { const response = await apiClient.get(`/reports/${item.id}/download`, { responseType: 'blob' }); const url = URL.createObjectURL(response.data); const link = document.createElement('a'); link.href = url; link.download = item.file_name ?? `reporte-${item.id}.pdf`; link.click(); URL.revokeObjectURL(url) }
