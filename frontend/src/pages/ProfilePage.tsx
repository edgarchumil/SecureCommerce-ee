import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { FormEvent, useState } from 'react'

import { changePassword } from '../api/administration'
import { getProfile, setupMfa, verifyMfa } from '../api/auth'
import { PasswordInput } from '../components/PasswordInput'
import { Page } from './OrganizationPage'

export function ProfilePage() {
  const client = useQueryClient()
  const [mfa, setMfa] = useState<{ secret: string; provisioning_uri: string } | null>(null)
  const profile = useQuery({ queryKey: ['profile'], queryFn: getProfile })
  const change = useMutation({ mutationFn: ({ current, next }: { current: string; next: string }) => changePassword(current, next) })
  const enableMfa = useMutation({ mutationFn: setupMfa, onSuccess: setMfa })
  const verify = useMutation({ mutationFn: verifyMfa, onSuccess: () => { setMfa(null); void client.invalidateQueries({ queryKey: ['profile'] }) } })
  const submit = (event: FormEvent<HTMLFormElement>) => { event.preventDefault(); const data = new FormData(event.currentTarget); change.mutate({ current: String(data.get('current')), next: String(data.get('next')) }) }
  return <Page title="Perfil" description="Revise su cuenta, contraseña y segundo factor."><div className="grid gap-5 lg:grid-cols-2"><section className="rounded-xl border bg-white p-5"><p><strong>{profile.data?.full_name}</strong></p><p>{profile.data?.email}</p><p className="text-sm text-slate-600">MFA: {profile.data?.mfa_enabled ? 'activado' : 'pendiente'}</p>{!profile.data?.mfa_enabled && !mfa && <button onClick={() => enableMfa.mutate()} className="mt-4 rounded-lg bg-blue-950 p-2 text-white">Configurar MFA</button>}{mfa && <form className="mt-4 grid gap-2" onSubmit={event => { event.preventDefault(); verify.mutate(String(new FormData(event.currentTarget).get('code'))) }}><p className="break-all text-sm">Agregue esta URI en su aplicación autenticadora: {mfa.provisioning_uri}</p><input aria-label="Código MFA" name="code" inputMode="numeric" pattern="[0-9]{6}" required className="rounded-lg border p-2"/><button className="rounded-lg bg-blue-950 p-2 text-white">Verificar y activar</button></form>}</section><form onSubmit={submit} className="grid gap-3 rounded-xl border bg-white p-5"><h2 className="font-semibold text-blue-950">Cambiar contraseña</h2><PasswordInput aria-label="Contraseña actual" name="current" autoComplete="current-password" required className="w-full rounded-lg border p-2"/><PasswordInput aria-label="Nueva contraseña" name="next" autoComplete="new-password" minLength={12} required className="w-full rounded-lg border p-2"/><button className="rounded-lg bg-blue-950 p-2 text-white">Cambiar contraseña</button>{change.isSuccess && <p role="status">Contraseña actualizada.</p>}</form></div></Page>
}
