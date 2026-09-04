import { zodResolver } from '@hookform/resolvers/zod'
import { AxiosError } from 'axios'
import { LockKeyhole, ShieldCheck } from 'lucide-react'
import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { Link, useNavigate } from 'react-router-dom'

import { login, type OrganizationOption } from '../api/auth'
import { PasswordInput } from '../components/PasswordInput'
import { useAuth } from '../features/auth/AuthContext'
import { loginSchema, type LoginValues } from '../schemas/auth'

export function LoginPage() {
  const [mfaRequired, setMfaRequired] = useState(false)
  const [serverError, setServerError] = useState('')
  const [organizations, setOrganizations] = useState<OrganizationOption[]>([])
  const [pendingValues, setPendingValues] = useState<LoginValues | null>(null)
  const { authenticate } = useAuth()
  const navigate = useNavigate()
  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm<LoginValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: { email: '', password: '', mfa_code: '' },
  })

  const submit = async (values: LoginValues) => {
    setServerError('')
    try {
      const result = await login({ ...values, mfa_code: values.mfa_code || undefined })
      if (result.mfa_required) {
        setMfaRequired(true)
        return
      }
      if (result.organization_selection_required) {
        setOrganizations(result.organizations)
        setPendingValues(values)
        return
      }
      authenticate(result.access_token)
      navigate('/panel', { replace: true })
    } catch (error) {
      setServerError(
        error instanceof AxiosError && error.response?.status === 401
          ? 'Correo o contraseña incorrectos.'
          : 'No fue posible iniciar sesión. Intente nuevamente.',
      )
    }
  }

  const chooseOrganization = async (organizationId: string) => {
    if (!pendingValues) return
    setServerError('')
    try {
      const result = await login({ ...pendingValues, organization_id: organizationId })
      authenticate(result.access_token)
      navigate('/panel', { replace: true })
    } catch {
      setServerError('No fue posible ingresar a la organización seleccionada.')
    }
  }

  return (
    <main className="grid min-h-screen place-items-center bg-slate-100 px-5 py-10">
      <section className="w-full max-w-md rounded-2xl border border-slate-200 bg-white p-7 shadow-sm">
        <div className="flex items-center gap-3 text-blue-950">
          <span className="rounded-xl bg-blue-950 p-2 text-white"><ShieldCheck aria-hidden="true" /></span>
          <div><h1 className="text-xl font-bold">Iniciar sesión</h1><p className="text-sm text-slate-600">SecureCommerce Advisor</p></div>
        </div>
        {organizations.length > 0 ? <div className="mt-7 space-y-3">
          <p className="font-semibold text-blue-950">Seleccione la empresa</p>
          <p className="text-sm text-slate-600">Su cuenta pertenece a más de una organización.</p>
          {organizations.map((item) => <button key={item.id} type="button" className="w-full rounded-lg border p-3 text-left hover:border-blue-500" onClick={() => void chooseOrganization(item.id)}><strong className="block">{item.name}</strong><span className="text-sm text-slate-500">{item.slug} · {item.role_code}</span></button>)}
          <button type="button" className="text-sm text-blue-700" onClick={() => { setOrganizations([]); setPendingValues(null) }}>Usar otra cuenta</button>
          {serverError && <p role="alert" className="text-sm text-red-800">{serverError}</p>}
        </div> : <form className="mt-7 space-y-5" onSubmit={handleSubmit(submit)} noValidate>
          <label className="block text-sm font-medium text-slate-800">
            Correo electrónico
            <input className="mt-2 w-full rounded-lg border border-slate-300 px-3 py-2.5" autoComplete="email" type="email" {...register('email')} />
            {errors.email && <span className="mt-1 block text-sm text-red-700">{errors.email.message}</span>}
          </label>
          <label className="block text-sm font-medium text-slate-800">
            Contraseña
            <PasswordInput className="mt-2 w-full rounded-lg border border-slate-300 px-3 py-2.5" autoComplete="current-password" {...register('password')} />
            {errors.password && <span className="mt-1 block text-sm text-red-700">{errors.password.message}</span>}
          </label>
          {mfaRequired && <label className="block text-sm font-medium text-slate-800">Código de verificación<input className="mt-2 w-full rounded-lg border border-slate-300 px-3 py-2.5 tracking-[0.35em]" autoComplete="one-time-code" inputMode="numeric" maxLength={6} {...register('mfa_code')} /><span className="mt-1 block text-xs text-slate-600">Ingrese el código de su aplicación autenticadora.</span></label>}
          {serverError && <p role="alert" className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-800">{serverError}</p>}
          <button className="flex w-full items-center justify-center gap-2 rounded-lg bg-blue-950 px-4 py-3 font-semibold text-white hover:bg-blue-900 disabled:opacity-60" disabled={isSubmitting} type="submit"><LockKeyhole size={18} aria-hidden="true" />{isSubmitting ? 'Verificando…' : mfaRequired ? 'Verificar código' : 'Ingresar'}</button>
          <Link className="block text-center text-sm text-blue-700" to="/recuperar-contrasena">¿Olvidó su contraseña?</Link>
          <Link className="block text-center text-sm font-semibold text-blue-700" to="/registro">Registrar una empresa</Link>
        </form>}
      </section>
    </main>
  )
}
