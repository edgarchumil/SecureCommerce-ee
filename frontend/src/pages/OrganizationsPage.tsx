import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Building2 } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { getMyOrganizations, selectOrganization } from '../api/auth'
import { useAuth } from '../features/auth/AuthContext'
import { Page } from './OrganizationPage'

export function OrganizationsPage() { const navigate = useNavigate(); const client = useQueryClient(); const { authenticate } = useAuth(); const query = useQuery({ queryKey: ['my-organizations'], queryFn: getMyOrganizations }); const select = useMutation({ mutationFn: selectOrganization, onSuccess: async (result) => { await client.cancelQueries(); client.clear(); authenticate(result.access_token); navigate('/panel', { replace: true }) } }); return <Page title="Mis empresas" description="Cambie el contexto de trabajo. Los datos permanecen separados por organización.">{query.isPending && <p>Cargando organizaciones…</p>}<div className="grid gap-4 sm:grid-cols-2">{query.data?.map(item => <button key={item.id} disabled={select.isPending} onClick={() => select.mutate(item.id)} className="rounded-xl border bg-white p-5 text-left hover:border-blue-500"><Building2 className="text-blue-700"/><strong className="mt-3 block text-lg text-blue-950">{item.name}</strong><span className="text-sm text-slate-500">{item.slug} · {item.role_code}</span></button>)}</div>{select.isError && <p className="mt-4 text-red-800">No fue posible cambiar de empresa.</p>}</Page> }
