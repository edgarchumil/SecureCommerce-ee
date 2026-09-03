import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { ArrowLeft, Plus, Search, X } from 'lucide-react'
import { FormEvent, useState } from 'react'
import { Link } from 'react-router-dom'

import { getAssets } from '../api/assets'
import { addTreatment, createRisk, getRisks, getThreats, getTreatments, getVulnerabilities } from '../api/risks'
import type { Risk, RiskLevel, RiskPayload } from '../types/risks'

const LEVELS: Record<RiskLevel, { label: string; style: string }> = {
  low: { label: 'Bajo', style: 'bg-emerald-100 text-emerald-900' },
  medium: { label: 'Medio', style: 'bg-amber-100 text-amber-900' },
  high: { label: 'Alto', style: 'bg-orange-100 text-orange-900' },
  critical: { label: 'Crítico', style: 'bg-red-100 text-red-900' },
}
const matrixLevel = (score: number): RiskLevel => score <= 4 ? 'low' : score <= 9 ? 'medium' : score <= 16 ? 'high' : 'critical'
type SelectItem = { id: string; name: string }

export function RisksPage() {
  const client = useQueryClient()
  const [search, setSearch] = useState(''); const [level, setLevel] = useState('')
  const [showForm, setShowForm] = useState(false); const [selected, setSelected] = useState<Risk | null>(null)
  const risks = useQuery({ queryKey: ['risks', search, level], queryFn: () => getRisks(search, level) })
  const assets = useQuery({ queryKey: ['assets', 'risk-form'], queryFn: () => getAssets() })
  const threats = useQuery({ queryKey: ['threats'], queryFn: getThreats })
  const vulnerabilities = useQuery({ queryKey: ['vulnerabilities'], queryFn: getVulnerabilities })
  const create = useMutation({ mutationFn: createRisk, onSuccess: () => { void client.invalidateQueries({ queryKey: ['risks'] }); setShowForm(false) } })
  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); const data = new FormData(event.currentTarget)
    const value = (name: string) => String(data.get(name) ?? ''); const optional = (name: string) => value(name) || null
    const payload: RiskPayload = { code: value('code'), title: value('title'), description: value('description'), asset_id: value('asset_id'), threat_id: optional('threat_id'), vulnerability_id: optional('vulnerability_id'), probability: Number(value('probability')), impact: Number(value('impact')), existing_controls: optional('existing_controls'), residual_probability: Number(value('residual_probability')), residual_impact: Number(value('residual_impact')), treatment_strategy: 'mitigate', responsible_user_id: null, target_date: optional('target_date'), progress: 0, status: 'identified' }
    create.mutate(payload)
  }
  return <main className="min-h-screen bg-slate-50 px-5 py-8"><section className="mx-auto max-w-6xl">
    <Link className="inline-flex items-center gap-2 text-sm text-blue-700" to="/panel"><ArrowLeft size={16} /> Panel</Link>
    <div className="mt-5 flex flex-col justify-between gap-4 sm:flex-row sm:items-end"><div><p className="text-sm font-semibold text-blue-700">Análisis y tratamiento</p><h1 className="mt-1 text-3xl font-bold text-blue-950">Registro de riesgos</h1><p className="mt-2 text-slate-600">Priorice amenazas con probabilidad e impacto.</p></div><button className="inline-flex items-center justify-center gap-2 rounded-lg bg-blue-950 px-4 py-3 font-semibold text-white" onClick={() => setShowForm(true)}><Plus size={18} /> Identificar riesgo</button></div>
    <RiskMatrix />
    <div className="mt-7 flex flex-wrap gap-3"><label className="relative min-w-64 flex-1"><span className="sr-only">Buscar riesgos</span><Search className="absolute left-3 top-3 text-slate-500" size={18} /><input className="w-full rounded-lg border border-slate-300 bg-white py-2.5 pl-10 pr-3" placeholder="Buscar por código o título" value={search} onChange={(e) => setSearch(e.target.value)} /></label><select aria-label="Filtrar por nivel" className="rounded-lg border border-slate-300 bg-white px-3" value={level} onChange={(e) => setLevel(e.target.value)}><option value="">Todos los niveles</option>{Object.entries(LEVELS).map(([key, item]) => <option key={key} value={key}>{item.label}</option>)}</select></div>
    {risks.isPending && <p className="mt-7">Cargando riesgos…</p>}{risks.isError && <p role="alert" className="mt-7 text-red-800">No fue posible cargar los riesgos.</p>}{risks.data?.items.length === 0 && <p className="mt-7 rounded-xl border border-dashed bg-white p-10 text-center">No hay riesgos registrados.</p>}
    {risks.data && risks.data.items.length > 0 && <div className="mt-7 overflow-x-auto rounded-xl border bg-white"><table className="w-full text-left text-sm"><thead className="bg-slate-100"><tr><th className="px-4 py-3">Riesgo</th><th className="px-4 py-3">Inherente</th><th className="px-4 py-3">Residual</th><th className="px-4 py-3">Avance</th><th className="px-4 py-3">Estado</th></tr></thead><tbody>{risks.data.items.map((risk) => <tr className="cursor-pointer border-t hover:bg-slate-50" key={risk.id} onClick={() => setSelected(risk)}><td className="px-4 py-3"><strong>{risk.title}</strong><p className="text-slate-500">{risk.code}</p></td><Score level={risk.inherent_level} score={risk.inherent_score} /><Score level={risk.residual_level} score={risk.residual_score} /><td className="px-4 py-3">{risk.progress}%</td><td className="px-4 py-3">{risk.status.replace('_', ' ')}</td></tr>)}</tbody></table></div>}
    {showForm && <RiskForm assets={assets.data?.items ?? []} threats={threats.data ?? []} vulnerabilities={vulnerabilities.data ?? []} pending={create.isPending} error={create.isError} onClose={() => setShowForm(false)} onSubmit={submit} />}{selected && <RiskDetail risk={selected} onClose={() => setSelected(null)} />}
  </section></main>
}

function Score({ level, score }: { level: RiskLevel; score: number }) { return <td className="px-4 py-3"><span className={`rounded-full px-2 py-1 font-semibold ${LEVELS[level].style}`}>{score} · {LEVELS[level].label}</span></td> }
function RiskMatrix() { return <section className="mt-7 rounded-xl border bg-white p-5"><h2 className="font-semibold text-blue-950">Matriz 5 × 5</h2><p className="mb-3 text-sm text-slate-500">Impacto → / Probabilidad ↓</p><div className="grid max-w-md grid-cols-5 gap-1">{[5,4,3,2,1].flatMap((probability) => [1,2,3,4,5].map((impact) => { const score = probability * impact; const level = matrixLevel(score); return <div key={`${probability}-${impact}`} title={`Probabilidad ${probability}, impacto ${impact}`} className={`flex aspect-square items-center justify-center rounded font-bold ${LEVELS[level].style}`}>{score}</div> }))}</div></section> }

function RiskForm({ assets, threats, vulnerabilities, pending, error, onClose, onSubmit }: { assets: SelectItem[]; threats: SelectItem[]; vulnerabilities: SelectItem[]; pending: boolean; error: boolean; onClose: () => void; onSubmit: (event: FormEvent<HTMLFormElement>) => void }) {
  return <div className="fixed inset-0 z-10 overflow-y-auto bg-slate-950/50 p-4"><form className="mx-auto max-w-2xl rounded-xl bg-white p-6" onSubmit={onSubmit}><div className="flex justify-between"><h2 className="text-xl font-bold text-blue-950">Identificar riesgo</h2><button type="button" aria-label="Cerrar" onClick={onClose}><X /></button></div><div className="mt-5 grid gap-4 sm:grid-cols-2"><Field name="code" label="Código" required /><Field name="title" label="Título" required /><label className="sm:col-span-2">Descripción<textarea name="description" required minLength={3} className="mt-1 min-h-20 w-full rounded-lg border p-2" /></label><Select name="asset_id" label="Activo" items={assets} required /><Select name="threat_id" label="Amenaza" items={threats} /><Select name="vulnerability_id" label="Vulnerabilidad" items={vulnerabilities} /><Scale name="probability" label="Probabilidad inherente" /><Scale name="impact" label="Impacto inherente" /><label className="sm:col-span-2">Controles existentes<textarea name="existing_controls" className="mt-1 min-h-16 w-full rounded-lg border p-2" /></label><Scale name="residual_probability" label="Probabilidad residual" /><Scale name="residual_impact" label="Impacto residual" /><Field name="target_date" label="Fecha objetivo" type="date" /></div>{error && <p role="alert" className="mt-4 text-red-800">Revise los datos e inténtelo de nuevo.</p>}<div className="mt-6 flex justify-end gap-3"><button type="button" className="px-4 py-2" onClick={onClose}>Cancelar</button><button disabled={pending || assets.length === 0} className="rounded-lg bg-blue-950 px-4 py-2 font-semibold text-white disabled:opacity-50">{pending ? 'Guardando…' : 'Guardar riesgo'}</button></div></form></div>
}
function Field({ name, label, type = 'text', required = false }: { name: string; label: string; type?: string; required?: boolean }) { return <label>{label}<input name={name} type={type} required={required} className="mt-1 w-full rounded-lg border p-2" /></label> }
function Select({ name, label, items, required = false }: { name: string; label: string; items: SelectItem[]; required?: boolean }) { return <label>{label}<select name={name} required={required} className="mt-1 w-full rounded-lg border p-2"><option value="">Seleccionar…</option>{items.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</select></label> }
function Scale({ name, label }: { name: string; label: string }) { return <label>{label}<select name={name} defaultValue="3" className="mt-1 w-full rounded-lg border p-2">{[1,2,3,4,5].map((value) => <option key={value}>{value}</option>)}</select></label> }

function RiskDetail({ risk, onClose }: { risk: Risk; onClose: () => void }) {
  const client = useQueryClient(); const [action, setAction] = useState('')
  const treatments = useQuery({ queryKey: ['risk-treatments', risk.id], queryFn: () => getTreatments(risk.id) })
  const add = useMutation({ mutationFn: () => addTreatment(risk.id, action, risk.progress), onSuccess: () => { setAction(''); void client.invalidateQueries({ queryKey: ['risk-treatments', risk.id] }); void client.invalidateQueries({ queryKey: ['risks'] }) } })
  return <div className="fixed inset-0 z-10 overflow-y-auto bg-slate-950/50 p-4"><aside className="ml-auto min-h-full max-w-xl bg-white p-6"><div className="flex justify-between"><div><p className="text-sm text-slate-500">{risk.code}</p><h2 className="text-2xl font-bold text-blue-950">{risk.title}</h2></div><button aria-label="Cerrar detalle" onClick={onClose}><X /></button></div><p className="mt-5">{risk.description}</p><div className="mt-5 grid grid-cols-2 gap-3"><div className="rounded-lg bg-slate-100 p-3">Riesgo inherente<br/><strong>{risk.inherent_score} · {LEVELS[risk.inherent_level].label}</strong></div><div className="rounded-lg bg-slate-100 p-3">Riesgo residual<br/><strong>{risk.residual_score} · {LEVELS[risk.residual_level].label}</strong></div></div><h3 className="mt-7 font-semibold">Plan de tratamiento</h3>{treatments.data?.map((item) => <article key={item.id} className="mt-3 rounded-lg border p-3"><p>{item.action}</p><p className="text-sm text-slate-500">Avance: {item.progress}%</p></article>)}<form className="mt-4" onSubmit={(event) => { event.preventDefault(); if (action.trim()) add.mutate() }}><label>Nueva acción<textarea value={action} onChange={(event) => setAction(event.target.value)} className="mt-1 min-h-20 w-full rounded-lg border p-2" /></label><button disabled={add.isPending || action.trim().length < 3} className="mt-2 rounded-lg bg-blue-950 px-4 py-2 font-semibold text-white disabled:opacity-50">Agregar acción</button></form></aside></div>
}
