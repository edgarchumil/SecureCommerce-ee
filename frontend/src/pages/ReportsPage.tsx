import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Building2, CheckCircle2, Download, FileText, LoaderCircle, Plus } from 'lucide-react'
import { useState, type FormEvent } from 'react'
import { getProfile } from '../api/auth'
import { createReport, downloadReport, getReports } from '../api/reports'
import { useAuth } from '../features/auth/AuthContext'
import type { ReportItem } from '../types/reports'

const statuses = { pending: 'En cola', processing: 'Generando PDF', completed: 'Disponible', failed: 'No generado' }
const date = (value: string) => new Date(value).toLocaleString('es-GT', { dateStyle: 'medium', timeStyle: 'short' })

export function ReportsPage() {
  const { token } = useAuth()
  const client = useQueryClient()
  const profile = useQuery({ queryKey: ['profile', token], queryFn: getProfile })
  const reports = useQuery({ queryKey: ['reports', token], queryFn: getReports,
    refetchInterval: (query) => query.state.data?.some(item => ['pending', 'processing'].includes(item.status)) ? 3000 : false })
  const [type, setType] = useState<'executive' | 'technical'>('executive')
  const [downloadError, setDownloadError] = useState('')
  const [downloading, setDownloading] = useState<string | null>(null)
  const create = useMutation({ mutationFn: ({ title, scope }: { title: string; scope: string }) => createReport(type, title, scope),
    onSuccess: () => void client.invalidateQueries({ queryKey: ['reports'] }) })
  const canCreate = ['superadmin', 'org_admin', 'analyst'].includes(profile.data?.role_code ?? '')
  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const data = new FormData(event.currentTarget)
    create.mutate({ title: String(data.get('title')).trim(), scope: String(data.get('scope')).trim() })
  }
  async function download(item: ReportItem) {
    setDownloadError(''); setDownloading(item.id)
    try { await downloadReport(item) } catch { setDownloadError('No fue posible descargar el PDF. Intente nuevamente.') }
    finally { setDownloading(null) }
  }
  return <main className="min-h-screen bg-slate-50 px-5 py-8 sm:px-8"><section className="mx-auto max-w-6xl">
    <div className="flex flex-wrap items-start justify-between gap-4"><div><p className="text-xs font-bold uppercase tracking-widest text-cyan-700">Información para decidir</p><h1 className="mt-2 text-3xl font-bold text-blue-950">Reportes PDF</h1><p className="mt-2 max-w-2xl text-slate-600">Convierta los registros de su empresa en un informe claro, con indicadores, riesgos y acciones de seguimiento.</p></div><span className="inline-flex items-center gap-2 rounded-xl border bg-white px-4 py-3 text-sm font-semibold text-blue-950"><Building2 size={18}/>{profile.data?.organization_name ?? 'Empresa seleccionada'}</span></div>
    {canCreate && <form className="mt-7 overflow-hidden rounded-2xl border bg-white shadow-sm" onSubmit={submit}>
      <div className="border-b bg-blue-950 px-6 py-5 text-white"><h2 className="text-lg font-semibold">Generar un informe</h2><p className="mt-1 text-sm text-slate-300">Sin portada adicional. Datos registrados al momento de generar el PDF.</p></div>
      <div className="space-y-5 p-6"><fieldset><legend className="mb-3 font-semibold text-blue-950">Seleccione el contenido</legend><div className="grid gap-3 sm:grid-cols-2">{(['executive', 'technical'] as const).map(option => <label key={option} className={`cursor-pointer rounded-xl border p-4 ${type === option ? 'border-cyan-600 bg-cyan-50' : 'border-slate-200'}`}><span className="flex items-center gap-2 font-semibold text-blue-950"><input type="radio" name="type" checked={type === option} onChange={() => setType(option)} value={option} />{option === 'executive' ? 'Ejecutivo' : 'Técnico'}</span><span className="mt-2 block text-sm leading-6 text-slate-600">{option === 'executive' ? 'Resumen para gerencia: indicadores, hasta 8 riesgos, 10 acciones, 6 activos críticos y 5 incidentes.' : 'Detalle completo: riesgos y controles, inventario, acciones de tratamiento e incidentes registrados.'}</span></label>)}</div></fieldset>
      <div className="grid gap-4 sm:grid-cols-2"><label className="text-sm font-semibold text-slate-700">Título del informe<input name="title" required minLength={3} maxLength={220} defaultValue="Diagnóstico de ciberseguridad" className="mt-2 w-full rounded-lg border p-3 font-normal" /></label><div className="rounded-lg bg-slate-50 p-3 text-sm leading-6 text-slate-600">Ambos formatos incluyen madurez por función NIST, responsables y fechas cuando estén registrados. Los campos faltantes se indican expresamente.</div></div>
      <label className="block text-sm font-semibold text-slate-700">Alcance declarado<textarea name="scope" required minLength={3} maxLength={2000} defaultValue="Activos, riesgos, controles e incidentes registrados para la empresa seleccionada." className="mt-2 min-h-20 w-full rounded-lg border p-3 font-normal" /><span className="mt-1 block text-xs font-normal text-slate-500">Describe el contexto del informe; no filtra los registros. La madurez corresponde a la última evaluación creada y conserva su estado de revisión.</span></label>
      <div className="flex flex-wrap items-center justify-between gap-3"><p className="text-xs text-slate-500">Para reflejar cambios posteriores, genere un nuevo informe.</p><button disabled={create.isPending} className="inline-flex items-center gap-2 rounded-lg bg-blue-950 px-5 py-3 font-semibold text-white disabled:opacity-60">{create.isPending ? <LoaderCircle size={18} className="animate-spin"/> : <Plus size={18}/>} {create.isPending ? 'Solicitando…' : 'Generar PDF'}</button></div>
      {create.isError && <p role="alert" className="text-sm text-red-800">No fue posible solicitar el reporte. Revise los campos e intente nuevamente.</p>}
      {create.isSuccess && <p role="status" className="flex items-center gap-2 text-sm text-emerald-800"><CheckCircle2 size={17}/>Solicitud recibida. El documento aparecerá disponible en el historial.</p>}</div>
    </form>}
    <div className="mb-4 mt-9 flex items-center justify-between"><h2 className="text-xl font-bold text-blue-950">Historial de informes</h2><span className="text-sm text-slate-500">{reports.data?.length ?? 0} documentos</span></div>
    {reports.isPending && <p role="status">Cargando reportes…</p>}
    {reports.isError && <p role="alert" className="rounded-xl border bg-white p-5 text-red-800">No se pudo cargar el historial. <button className="underline" onClick={() => void reports.refetch()}>Reintentar</button></p>}
    {downloadError && <p role="alert" className="mb-3 text-red-800">{downloadError}</p>}
    {reports.data?.length === 0 && <div className="rounded-xl border border-dashed bg-white p-8 text-center"><FileText className="mx-auto text-cyan-700" size={30}/><p className="mt-3 font-semibold text-blue-950">Todavía no hay informes</p><p className="mt-1 text-sm text-slate-500">{canCreate ? 'Genere el primer PDF con los datos de esta empresa.' : 'Los informes generados por su equipo aparecerán aquí.'}</p></div>}
    <div className="space-y-3">{reports.data?.map(item => <article key={item.id} className="flex flex-col justify-between gap-4 rounded-xl border bg-white p-5 sm:flex-row sm:items-center"><div className="min-w-0"><div className="flex flex-wrap items-center gap-2"><FileText size={19} className="text-cyan-700"/><h3 className="break-words font-semibold text-blue-950">{item.title}</h3><span className={`rounded-full px-2.5 py-1 text-xs font-semibold ${item.status === 'completed' ? 'bg-emerald-50 text-emerald-800' : item.status === 'failed' ? 'bg-red-50 text-red-800' : 'bg-amber-50 text-amber-800'}`}>{statuses[item.status]}</span></div><p className="mt-2 text-sm text-slate-500">{item.report_type === 'executive' ? 'Ejecutivo' : 'Técnico'} · {date(item.created_at)}{item.size_bytes ? ` · ${Math.ceil(item.size_bytes / 1024)} KB` : ''}</p><p className="mt-1 break-words text-sm text-slate-600">{item.scope}</p>{item.error_message && <p className="mt-2 text-sm text-red-800">{item.error_message}</p>}</div><button disabled={item.status !== 'completed' || downloading !== null} className="inline-flex shrink-0 items-center justify-center gap-2 rounded-lg border px-4 py-2 text-sm font-semibold text-blue-950 hover:bg-slate-50 disabled:opacity-50" onClick={() => void download(item)}>{downloading === item.id ? <LoaderCircle size={17} className="animate-spin"/> : <Download size={17}/>}Descargar PDF</button></article>)}</div>
  </section></main>
}
