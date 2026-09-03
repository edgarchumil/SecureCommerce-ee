import { useQuery } from '@tanstack/react-query'
import { BarChart3, Building2, ChevronDown, ClipboardCheck, FileText, Gauge, LogOut, Menu, Settings, ShieldCheck, Siren, UserCog, Users, X } from 'lucide-react'
import { useEffect, useState, type ReactNode } from 'react'
import { NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom'
import { getProfile } from '../api/auth'
import { useAuth } from '../features/auth/AuthContext'

type MenuItem = { to: string; label: string; icon: typeof Gauge }
const primary: MenuItem[] = [
  { to: '/panel', label: 'Panel ejecutivo', icon: Gauge }, { to: '/activos', label: 'Inventario de activos', icon: ClipboardCheck }, { to: '/incidentes', label: 'Incidentes', icon: Siren },
]
const groups = [
  { label: 'Evaluación y riesgo', icon: ShieldCheck, items: [
    { to: '/evaluaciones', label: 'Evaluación NIST', icon: ClipboardCheck }, { to: '/cumplimiento', label: 'Cumplimiento NIST', icon: BarChart3 }, { to: '/riesgos', label: 'Gestión de riesgos', icon: ShieldCheck }, { to: '/recomendaciones', label: 'Recomendaciones', icon: ClipboardCheck },
  ]},
  { label: 'Informes y control', icon: FileText, items: [
    { to: '/reportes', label: 'Reportes PDF', icon: FileText }, { to: '/auditoria', label: 'Auditoría', icon: ClipboardCheck }, { to: '/sesiones', label: 'Sesiones activas', icon: Users },
  ]},
  { label: 'Administración', icon: Settings, items: [
    { to: '/organizacion', label: 'Organización', icon: Building2 }, { to: '/usuarios', label: 'Usuarios y roles', icon: UserCog }, { to: '/configuracion', label: 'Configuración', icon: Settings }, { to: '/perfil', label: 'Mi perfil', icon: Users }, { to: '/organizaciones', label: 'Cambiar empresa', icon: Building2 },
  ]},
]

function Navigation({ superadmin, close }: { superadmin: boolean; close: () => void }) {
  const location = useLocation()
  const [opened, setOpened] = useState<Record<string, boolean>>(() => Object.fromEntries(groups.map(g => [g.label, g.items.some(i => location.pathname.startsWith(i.to))])))
  const linkClass = ({ isActive }: { isActive: boolean }) => `flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition ${isActive ? 'bg-cyan-400 text-slate-950 shadow-sm' : 'text-slate-300 hover:bg-white/10 hover:text-white'}`
  return <nav aria-label="Navegación principal" className="space-y-1 px-3 py-4">
    {primary.map(item => <NavLink key={item.to} to={item.to} onClick={close} className={linkClass}><item.icon size={18} />{item.label}</NavLink>)}
    <div className="my-3 border-t border-white/10" />
    {groups.map(group => { const expanded = opened[group.label] ?? false; const active = group.items.some(i => location.pathname.startsWith(i.to)); return <div key={group.label}>
      <button type="button" aria-expanded={expanded} onClick={() => setOpened(v => ({ ...v, [group.label]: !expanded }))} className={`flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-left text-sm font-semibold transition ${active ? 'text-cyan-300' : 'text-slate-300 hover:bg-white/10 hover:text-white'}`}><group.icon size={18} /><span className="flex-1">{group.label}</span><ChevronDown size={16} className={`transition-transform ${expanded ? 'rotate-180' : ''}`} /></button>
      {expanded && <div className="ml-4 space-y-1 border-l border-white/15 py-1 pl-3">{group.items.map(item => <NavLink key={item.to} to={item.to} onClick={close} className={linkClass}><item.icon size={16} />{item.label}</NavLink>)}</div>}
    </div>})}
    {superadmin && <><div className="my-3 border-t border-white/10" /><NavLink to="/plataforma" onClick={close} className={linkClass}><Building2 size={18} />Administración de plataforma</NavLink></>}
  </nav>
}

export function AppShell() {
  const [mobileOpen, setMobileOpen] = useState(false); const location = useLocation(); const navigate = useNavigate(); const { signOut } = useAuth()
  const profile = useQuery({ queryKey: ['profile'], queryFn: getProfile })
  useEffect(() => setMobileOpen(false), [location.pathname])
  const sidebar = <div className="flex h-full flex-col bg-[#071d38] text-white"><div className="flex h-20 items-center gap-3 border-b border-white/10 px-5"><span className="grid h-10 w-10 place-items-center rounded-xl bg-cyan-400 text-slate-950"><ShieldCheck /></span><div><strong className="block text-sm">SecureCommerce</strong><span className="text-xs text-slate-400">Advisor</span></div></div><div className="flex-1 overflow-y-auto"><Navigation superadmin={Boolean(profile.data?.is_superadmin)} close={() => setMobileOpen(false)} /></div><div className="border-t border-white/10 p-3"><div className="mb-2 px-3"><p className="truncate text-sm font-semibold">{profile.data?.full_name ?? 'Usuario'}</p><p className="truncate text-xs text-slate-400">{profile.data?.email}</p></div><button className="flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-sm text-slate-300 hover:bg-white/10 hover:text-white" onClick={() => void signOut().then(() => navigate('/login'))}><LogOut size={18} />Cerrar sesión</button></div></div>
  return <div className="min-h-screen bg-slate-50 lg:pl-72"><aside className="fixed inset-y-0 left-0 z-40 hidden w-72 lg:block">{sidebar}</aside>{mobileOpen && <div className="fixed inset-0 z-50 lg:hidden"><button aria-label="Cerrar menú" className="absolute inset-0 bg-slate-950/60" onClick={() => setMobileOpen(false)} /><aside className="relative h-full w-72 shadow-2xl">{sidebar}<button aria-label="Cerrar menú" className="absolute right-3 top-3 rounded-lg p-2 text-white" onClick={() => setMobileOpen(false)}><X /></button></aside></div>}<header className="sticky top-0 z-30 flex h-16 items-center border-b bg-white/95 px-4 backdrop-blur lg:hidden"><button aria-label="Abrir menú" className="rounded-lg border p-2 text-blue-950" onClick={() => setMobileOpen(true)}><Menu /></button><span className="ml-3 font-bold text-blue-950">SecureCommerce Advisor</span></header><Outlet /></div>
}

export function ContentPage({ title, description, children }: { title: string; description: string; children: ReactNode }) { return <main className="px-5 py-8 sm:px-8"><section className="mx-auto max-w-7xl"><h1 className="text-3xl font-bold text-blue-950">{title}</h1><p className="mb-6 mt-2 text-slate-600">{description}</p>{children}</section></main> }
