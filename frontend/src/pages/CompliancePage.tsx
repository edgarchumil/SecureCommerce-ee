import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { getEvaluations } from '../api/evaluations'
import { Page } from './OrganizationPage'
export function CompliancePage(){const query=useQuery({queryKey:['evaluations','compliance'],queryFn:getEvaluations});return <Page title="Cumplimiento NIST CSF 2.0" description="Perfil actual, objetivo y brechas por evaluación."><div className="grid gap-3">{query.data?.map(item=><Link key={item.id} to={`/evaluaciones/${item.id}/resultados`} className="rounded-xl border bg-white p-4"><strong>{item.name}</strong><p className="text-sm text-slate-600">Objetivo de madurez: {item.target_maturity}/4 · Estado: {item.status}</p></Link>)}</div></Page>}
