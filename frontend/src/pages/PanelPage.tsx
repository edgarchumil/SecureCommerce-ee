import { useQuery } from '@tanstack/react-query'
import { Activity, Boxes, ShieldAlert } from 'lucide-react'
import { useState } from 'react'
import { Bar, BarChart, CartesianGrid, Cell, Line, LineChart, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'

import { getProfile } from '../api/auth'
import { getDashboard } from '../api/dashboard'
import type { ChartPoint, DashboardFilters } from '../types/dashboard'

const COLORS = ['#0369a1', '#0d9488', '#d97706', '#dc2626', '#7c3aed', '#475569']
const ASSET_TYPES = [
  ['server', 'Servidor'], ['computer', 'Computadora'], ['mobile', 'Móvil'], ['network', 'Red'],
  ['application', 'Aplicación'], ['database', 'Base de datos'], ['information', 'Información'],
  ['cloud_service', 'Servicio en la nube'], ['critical_account', 'Cuenta crítica'], ['supplier', 'Proveedor'], ['other', 'Otro'],
]
const ROLE_LABELS: Record<string, string> = {
  org_admin: 'Administrador', security_analyst: 'Analista de seguridad', auditor: 'Auditor', viewer: 'Consulta',
}

export function PanelPage() {
  const profile = useQuery({ queryKey: ['profile'], queryFn: getProfile })
  const [filters, setFilters] = useState<DashboardFilters>({ dateFrom: '', dateTo: '', assetType: '' })
  const dashboard = useQuery({ queryKey: ['dashboard', filters], queryFn: () => getDashboard(filters) })
  const update = (key: keyof DashboardFilters, value: string) => setFilters((current) => ({ ...current, [key]: value }))
  return <main className="px-5 py-8 sm:px-8">
    <section className="mx-auto max-w-7xl"><p className="text-sm font-semibold text-blue-700">Resumen ejecutivo</p><h1 className="mt-1 text-3xl font-bold text-blue-950">{profile.data ? `${ROLE_LABELS[profile.data.role_code ?? ''] ?? profile.data.role_code ?? 'Usuario'} - ${profile.data.organization_name ?? 'Sin empresa seleccionada'}` : 'Rol - Empresa'}</h1>
      <form className="mt-6 grid gap-3 rounded-xl border bg-white p-4 sm:grid-cols-4" aria-label="Filtros del panel" onSubmit={(event) => event.preventDefault()}><label>Desde<input aria-label="Fecha inicial" className="mt-1 w-full rounded-lg border p-2" type="date" value={filters.dateFrom} onChange={(event) => update('dateFrom', event.target.value)} /></label><label>Hasta<input aria-label="Fecha final" className="mt-1 w-full rounded-lg border p-2" type="date" value={filters.dateTo} onChange={(event) => update('dateTo', event.target.value)} /></label><label>Tipo de activo<select className="mt-1 w-full rounded-lg border p-2" value={filters.assetType} onChange={(event) => update('assetType', event.target.value)}><option value="">Todos</option>{ASSET_TYPES.map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label><button type="button" className="self-end rounded-lg border px-4 py-2" onClick={() => setFilters({ dateFrom: '', dateTo: '', assetType: '' })}>Limpiar filtros</button></form>
      {dashboard.isPending && <DashboardSkeleton />}{dashboard.isError && <div role="alert" className="mt-6 rounded-xl border border-red-200 bg-red-50 p-5 text-red-900"><ShieldAlert className="inline" /> No fue posible cargar los indicadores. Revise la conexión e inténtelo de nuevo.</div>}
      {dashboard.data && <><div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-5">{dashboard.data.kpis.map((metric, index) => <article key={metric.key} className="rounded-xl border bg-white p-5"><div className="flex items-center justify-between text-slate-500"><span>{metric.label}</span>{index % 2 ? <Activity size={19} /> : <Boxes size={19} />}</div><p className="mt-2 text-3xl font-bold text-blue-950">{metric.value}{metric.unit}</p></article>)}</div>
        <div className="mt-6 grid gap-5 lg:grid-cols-2"><Chart title="Activos por tipo" data={dashboard.data.assets_by_type} kind="bar" /><Chart title="Riesgos por nivel" data={dashboard.data.risks_by_level} kind="pie" /><Chart title="Estados de evaluación" data={dashboard.data.evaluations_by_status} kind="bar" /><Chart title="Riesgos identificados por mes" data={dashboard.data.risks_over_time} kind="line" /></div>
      </>}
    </section>
  </main>
}

function DashboardSkeleton() { return <div role="status" className="mt-6 grid animate-pulse gap-4 sm:grid-cols-2 lg:grid-cols-5"><span className="sr-only">Cargando indicadores</span>{[1,2,3,4,5].map((item) => <div key={item} className="h-28 rounded-xl bg-slate-200" />)}</div> }

function Chart({ title, data, kind }: { title: string; data: ChartPoint[]; kind: 'bar' | 'pie' | 'line' }) {
  return <section className="rounded-xl border bg-white p-5"><h2 className="font-semibold text-blue-950">{title}</h2>{data.length === 0 ? <p className="mt-8 text-center text-slate-500">Sin datos para los filtros seleccionados.</p> : <div className="mt-4 h-64" role="img" aria-label={`${title}: ${data.map((item) => `${item.label}, ${item.value}`).join('; ')}`}><ResponsiveContainer width="100%" height="100%">{kind === 'pie' ? <PieChart><Pie data={data} dataKey="value" nameKey="label" outerRadius={90}>{data.map((item, index) => <Cell key={item.key} fill={COLORS[index % COLORS.length]} />)}</Pie><Tooltip /></PieChart> : kind === 'line' ? <LineChart data={data}><CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="label" /><YAxis allowDecimals={false} /><Tooltip /><Line dataKey="value" name="Riesgos" stroke="#0369a1" strokeWidth={3} /></LineChart> : <BarChart data={data}><CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="label" /><YAxis allowDecimals={false} /><Tooltip /><Bar dataKey="value" name="Total" fill="#0369a1" /></BarChart>}</ResponsiveContainer></div>}<table className="sr-only"><caption>Datos de {title}</caption><thead><tr><th>Categoría</th><th>Valor</th></tr></thead><tbody>{data.map((item) => <tr key={item.key}><td>{item.label}</td><td>{item.value}</td></tr>)}</tbody></table></section>
}
