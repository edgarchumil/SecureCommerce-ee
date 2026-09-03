import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { ArrowLeft, Laptop, XCircle } from 'lucide-react'
import { Link } from 'react-router-dom'

import { getSessions, revokeSession } from '../api/auth'

export function SessionsPage() {
  const queryClient = useQueryClient()
  const sessions = useQuery({ queryKey: ['sessions'], queryFn: getSessions })
  const revoke = useMutation({
    mutationFn: revokeSession,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['sessions'] }),
  })
  return (
    <main className="min-h-screen bg-slate-50 px-6 py-10">
      <section className="mx-auto max-w-4xl">
        <Link className="inline-flex items-center gap-2 text-sm text-blue-700" to="/panel"><ArrowLeft size={16} />Volver al panel</Link>
        <h1 className="mt-5 text-3xl font-bold text-blue-950">Sesiones activas</h1>
        <p className="mt-2 text-slate-600">Revise dónde ha iniciado sesión y revoque accesos que no reconozca.</p>
        {sessions.isPending && <p className="mt-8">Cargando sesiones…</p>}
        {sessions.isError && <p role="alert" className="mt-8 text-red-800">No fue posible cargar las sesiones.</p>}
        <ul className="mt-8 space-y-3">
          {sessions.data?.map((session) => (
            <li key={session.id} className="flex flex-col justify-between gap-4 rounded-xl border border-slate-200 bg-white p-5 sm:flex-row sm:items-center">
              <div className="flex gap-3"><Laptop className="mt-1 text-blue-700" aria-hidden="true" /><div><p className="font-semibold text-slate-900">{session.user_agent || 'Dispositivo sin identificar'}</p><p className="mt-1 text-sm text-slate-600">Creada: {new Date(session.created_at).toLocaleString('es-GT')} · IP: {session.ip_address || 'No disponible'}</p><p className="mt-1 text-sm">Estado: {session.revoked_at ? 'Revocada' : 'Activa'}</p></div></div>
              {!session.revoked_at && <button className="inline-flex items-center justify-center gap-2 rounded-lg border border-red-300 px-3 py-2 text-sm font-semibold text-red-800 hover:bg-red-50" disabled={revoke.isPending} onClick={() => revoke.mutate(session.id)}><XCircle size={17} />Revocar</button>}
            </li>
          ))}
        </ul>
      </section>
    </main>
  )
}
