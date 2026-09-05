import { useQuery } from '@tanstack/react-query'
import { getRiskBands } from '../api/risks'
import { Page } from './OrganizationPage'

const labels = { low: 'Bajo', medium: 'Medio', high: 'Alto', critical: 'Crítico' }

export function SettingsPage() {
  const bands = useQuery({ queryKey: ['risk-bands'], queryFn: getRiskBands })
  return <Page title="Configuración" description="Parámetros operativos de la empresa seleccionada.">
    <section className="max-w-2xl rounded-xl border bg-white p-5">
      <h2 className="font-semibold text-blue-950">Clasificación de riesgo</h2>
      {bands.isPending && <p className="mt-3">Cargando escala…</p>}
      {bands.isError && <p role="alert" className="mt-3 text-red-800">No fue posible cargar la escala de riesgo.</p>}
      <ul className="mt-3 list-disc space-y-1 pl-6">{bands.data?.map(band => <li key={band.level}>{labels[band.level]}: {band.minimum}–{band.maximum}</li>)}</ul>
      <h2 className="mt-6 font-semibold text-blue-950">Seguridad</h2>
      <p className="mt-2 text-slate-600">Los secretos, IA, almacenamiento y backups se administran mediante variables de entorno. Los cambios sensibles requieren despliegue controlado.</p>
    </section>
  </Page>
}
