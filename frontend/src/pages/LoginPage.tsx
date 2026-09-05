import { zodResolver } from '@hookform/resolvers/zod'
import { AxiosError } from 'axios'
import { LockKeyhole, ShieldCheck } from 'lucide-react'
import { useEffect, useState } from 'react'
import { useForm } from 'react-hook-form'
import { Link, useLocation, useNavigate } from 'react-router-dom'

import { login, type OrganizationOption } from '../api/auth'
import { PasswordInput } from '../components/PasswordInput'
import { useAuth } from '../features/auth/AuthContext'
import { loginSchema, type LoginValues } from '../schemas/auth'
import { RegisterPage } from './RegisterPage'
import { BrandLoading } from '../components/BrandLoading'

export function LoginPage() {
  const location = useLocation()
  const [entryLoading, setEntryLoading] = useState(location.state?.showLoading === true)
  useEffect(() => {
    if (!entryLoading) return
    const timer = window.setTimeout(() => setEntryLoading(false), 2000)
    return () => window.clearTimeout(timer)
  }, [entryLoading])
  const [mfaRequired, setMfaRequired] = useState(false)
  const [loading, setLoading] = useState(false)
  const [serverError, setServerError] = useState('')
  const [organizations, setOrganizations] = useState<OrganizationOption[]>([])
  const [pendingValues, setPendingValues] = useState<LoginValues | null>(null)
  const [registering, setRegistering] = useState(false)
  const [openingRegistration, setOpeningRegistration] = useState(false)
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
      setLoading(true)
      await new Promise<void>((resolve) => window.setTimeout(resolve, 2000))
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
    } finally {
      setLoading(false)
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

  const adminOrganization = organizations.find((item) => ['org_admin', 'superadmin'].includes(item.role_code))
  const openRegistration = async () => {
    if (!pendingValues || !adminOrganization || openingRegistration) return
    setOpeningRegistration(true)
    setServerError('')
    try {
      const result = await login({ ...pendingValues, organization_id: adminOrganization.id })
      if (!result.access_token || result.mfa_required) throw new Error('Sesión no disponible')
      authenticate(result.access_token)
      setRegistering(true)
    } catch {
      setServerError('No fue posible abrir el registro. Intente iniciar sesión nuevamente.')
    } finally {
      setOpeningRegistration(false)
    }
  }

  if (entryLoading) return <BrandLoading message="Preparando el acceso" />
  if (loading) return <BrandLoading message="Iniciando sesión" />
  if (registering) return <RegisterPage onBack={() => setRegistering(false)} />

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
          {adminOrganization && <button type="button" disabled={openingRegistration} className="w-full rounded-lg bg-blue-950 px-4 py-3 font-semibold text-white hover:bg-blue-900 disabled:opacity-60" onClick={() => void openRegistration()}>{openingRegistration ? 'Verificando permisos…' : 'Registrar una empresa'}</button>}
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
          <Link className="block w-full rounded-lg border border-slate-300 px-4 py-3 text-center text-sm font-semibold text-blue-950 transition hover:border-blue-900 hover:bg-slate-50 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-700" to="/">Volver al inicio</Link>
        </form>}
      </section>
    </main>
  )
}
