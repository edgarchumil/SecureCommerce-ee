import { Activity } from 'lucide-react'

export type HealthState = 'loading' | 'available' | 'error'

export function HealthStatusCard({ state }: { state: HealthState }) {
  return (
    <aside className="self-start rounded-2xl border border-slate-200 bg-white p-6 shadow-sm" aria-live="polite">
      <div className="flex items-center justify-between">
        <h2 className="font-semibold text-blue-950">Estado de la plataforma</h2>
        <Activity className="text-blue-700" aria-hidden="true" />
      </div>
      {state === 'loading' && <p className="mt-5 text-slate-600">Verificando conexión…</p>}
      {state === 'error' && (
        <div className="mt-5 rounded-lg border border-red-200 bg-red-50 p-4">
          <p className="font-semibold text-red-900">API no disponible</p>
          <p className="mt-1 text-sm text-red-800">Revise que los servicios estén en ejecución.</p>
        </div>
      )}
      {state === 'available' && (
        <div className="mt-5 rounded-lg border border-green-200 bg-green-50 p-4">
          <p className="font-semibold text-green-900">API disponible</p>
          <p className="mt-1 text-sm text-green-800">La base técnica está funcionando correctamente.</p>
        </div>
      )}
      <p className="mt-5 text-sm leading-6 text-slate-600">
        MVP operativo: identidad, evaluaciones, riesgos, recomendaciones, panel y reportes.
      </p>
    </aside>
  )
}
