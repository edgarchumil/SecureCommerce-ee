import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { FormEvent, type ReactNode } from 'react'
import { ContentPage } from '../components/AppShell'
import { getOrganization, updateOrganization } from '../api/administration'

export function OrganizationPage() {
  const client = useQueryClient(); const query = useQuery({ queryKey: ['organization'], queryFn: getOrganization })
  const update = useMutation({ mutationFn: updateOrganization, onSuccess: () => void client.invalidateQueries({ queryKey: ['organization'] }) })
  const submit = (event: FormEvent<HTMLFormElement>) => { event.preventDefault(); const data = new FormData(event.currentTarget); update.mutate({ name: String(data.get('name')), sector: String(data.get('sector')), size: String(data.get('size')), country: String(data.get('country')) }) }
  return <Page title="Organización" description="Datos generales de su empresa.">{query.data && <form onSubmit={submit} className="grid max-w-2xl gap-4 rounded-xl border bg-white p-6 sm:grid-cols-2"><Field name="name" label="Nombre" value={query.data.name}/><Field name="sector" label="Sector" value={query.data.sector ?? ''}/><Field name="size" label="Tamaño" value={query.data.size ?? ''}/><Field name="country" label="País (código ISO)" value={query.data.country}/><button className="rounded-lg bg-blue-950 px-4 py-2 text-white sm:col-span-2" disabled={update.isPending}>Guardar cambios</button>{update.isSuccess && <p role="status">Organización actualizada.</p>}</form>}</Page>
}
export function Page({ title, description, children }: { title: string; description: string; children: ReactNode }) { return <ContentPage title={title} description={description}>{children}</ContentPage> }
function Field({ name, label, value }: { name: string; label: string; value: string }) { return <label>{label}<input className="mt-1 w-full rounded-lg border p-2" name={name} defaultValue={value} required /></label> }
