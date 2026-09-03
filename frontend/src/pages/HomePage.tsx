import { ArrowRight, BarChart3, Bot, Boxes, Check, ChevronRight, ClipboardCheck, FileText, LockKeyhole, Menu, ShieldCheck, Sparkles, X } from 'lucide-react'
import { useState } from 'react'
import { Link } from 'react-router-dom'

const capabilities = [
  { icon: Boxes, title: 'Inventario de activos', description: 'Centralice equipos, sistemas, aplicaciones y datos críticos para saber exactamente qué debe proteger.' },
  { icon: ClipboardCheck, title: 'Evaluación NIST CSF 2.0', description: 'Conozca su nivel de madurez mediante una evaluación guiada, práctica y fácil de comprender.' },
  { icon: BarChart3, title: 'Riesgos priorizados', description: 'Visualice probabilidad, impacto y criticidad para enfocar sus recursos donde realmente importan.' },
  { icon: Bot, title: 'Recomendaciones con IA', description: 'Convierta hallazgos técnicos en acciones claras, ordenadas y adaptadas a la realidad de su empresa.' },
  { icon: FileText, title: 'Reportes ejecutivos', description: 'Genere informes PDF listos para compartir con gerencia, auditoría y responsables de tecnología.' },
  { icon: ShieldCheck, title: 'Seguimiento continuo', description: 'Mantenga visible su avance, documente mejoras y fortalezca su postura de seguridad en el tiempo.' },
]

export function HomePage() {
  const [menuOpen, setMenuOpen] = useState(false)

  return (
    <main className="landing min-h-screen overflow-hidden bg-[#f7fafc] text-slate-950">
      <header className="fixed inset-x-0 top-0 z-50 border-b border-white/10 bg-[#061b35]/90 text-white backdrop-blur-xl">
        <div className="mx-auto flex h-20 max-w-7xl items-center justify-between px-5 sm:px-8">
          <Link className="flex items-center gap-3" to="/" aria-label="SecureCommerce Advisor, inicio">
            <span className="grid size-10 place-items-center rounded-xl bg-cyan-400 text-[#061b35] shadow-[0_0_28px_rgba(34,211,238,.25)]"><ShieldCheck size={25} strokeWidth={2.3} aria-hidden="true" /></span>
            <span className="leading-tight"><span className="block text-base font-bold tracking-tight sm:text-lg">SecureCommerce</span><span className="block text-[10px] font-semibold uppercase tracking-[0.26em] text-cyan-300">Advisor</span></span>
          </Link>
          <nav className="hidden items-center gap-8 text-sm font-medium text-slate-200 md:flex" aria-label="Navegación principal">
            <a className="transition hover:text-cyan-300" href="#solucion">Solución</a><a className="transition hover:text-cyan-300" href="#como-funciona">Cómo funciona</a><a className="transition hover:text-cyan-300" href="#beneficios">Beneficios</a>
          </nav>
          <div className="hidden items-center gap-3 md:flex"><Link className="text-sm font-semibold text-cyan-300" to="/registro">Registrar empresa</Link><Link className="inline-flex items-center gap-2 rounded-xl border border-cyan-300/40 px-5 py-2.5 text-sm font-semibold transition hover:border-cyan-300 hover:bg-cyan-300 hover:text-[#061b35]" to="/login"><LockKeyhole size={16} aria-hidden="true" /> Iniciar sesión</Link></div>
          <button className="rounded-lg p-2 md:hidden" type="button" aria-label={menuOpen ? 'Cerrar menú' : 'Abrir menú'} aria-expanded={menuOpen} onClick={() => setMenuOpen(!menuOpen)}>{menuOpen ? <X /> : <Menu />}</button>
        </div>
        {menuOpen && <nav className="border-t border-white/10 bg-[#061b35] px-5 py-5 md:hidden" aria-label="Navegación móvil"><div className="mx-auto flex max-w-7xl flex-col gap-4 text-sm text-slate-200"><a href="#solucion" onClick={() => setMenuOpen(false)}>Solución</a><a href="#como-funciona" onClick={() => setMenuOpen(false)}>Cómo funciona</a><a href="#beneficios" onClick={() => setMenuOpen(false)}>Beneficios</a><Link className="mt-2 flex items-center justify-center gap-2 rounded-xl bg-cyan-400 px-5 py-3 font-bold text-[#061b35]" to="/login">Iniciar sesión <ArrowRight size={17} /></Link></div></nav>}
      </header>

      <section className="hero-grid relative bg-[#061b35] pb-24 pt-32 text-white sm:pb-32 sm:pt-40">
        <div className="hero-glow absolute inset-0" aria-hidden="true" />
        <div className="relative mx-auto grid max-w-7xl items-center gap-14 px-5 sm:px-8 lg:grid-cols-[1.03fr_.97fr]">
          <div>
            <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-cyan-300/25 bg-cyan-300/10 px-4 py-2 text-xs font-bold uppercase tracking-[0.14em] text-cyan-300"><Sparkles size={14} aria-hidden="true" /> Ciberseguridad inteligente para MIPYMES</div>
            <h1 className="max-w-3xl text-4xl font-extrabold leading-[1.08] tracking-[-0.035em] sm:text-6xl lg:text-[4.15rem]">Proteja su empresa.<br /><span className="text-cyan-300">Decida con claridad.</span></h1>
            <p className="mt-6 max-w-2xl text-lg leading-8 text-slate-300 sm:text-xl">Identifique sus activos críticos, evalúe riesgos y reciba recomendaciones claras con apoyo de inteligencia artificial, desde una sola plataforma.</p>
            <div className="mt-9 flex flex-col gap-3 sm:flex-row">
              <Link className="inline-flex items-center justify-center gap-2 rounded-xl bg-cyan-400 px-6 py-3.5 font-bold text-[#061b35] shadow-[0_16px_45px_rgba(34,211,238,.18)] transition hover:-translate-y-0.5 hover:bg-cyan-300" to="/registro">Registrar mi empresa <ArrowRight size={18} aria-hidden="true" /></Link>
              <a className="inline-flex items-center justify-center gap-2 rounded-xl border border-white/20 px-6 py-3.5 font-semibold transition hover:border-white/45 hover:bg-white/5" href="#solucion">Conocer la solución <ChevronRight size={18} aria-hidden="true" /></a>
            </div>
            <div className="mt-9 flex flex-wrap gap-x-6 gap-y-3 text-sm text-slate-300">{['En español', 'Basado en NIST CSF 2.0', 'Diseñado para Guatemala'].map((item) => <span className="flex items-center gap-2" key={item}><Check className="text-cyan-300" size={17} strokeWidth={3} /> {item}</span>)}</div>
          </div>

          <div className="dashboard-shell relative mx-auto w-full max-w-[590px]">
            <div className="absolute -left-8 top-16 size-28 rounded-full bg-cyan-400/20 blur-3xl" aria-hidden="true" />
            <div className="relative overflow-hidden rounded-[1.6rem] border border-white/15 bg-[#0a2544]/85 p-3 shadow-2xl shadow-black/30 backdrop-blur">
              <div className="flex items-center gap-2 border-b border-white/10 px-3 pb-3 pt-1"><span className="size-2.5 rounded-full bg-red-400/80" /><span className="size-2.5 rounded-full bg-amber-300/80" /><span className="size-2.5 rounded-full bg-emerald-400/80" /><span className="ml-auto text-[10px] font-semibold uppercase tracking-[.2em] text-slate-400">Panel de seguridad</span></div>
              <div className="grid gap-3 p-2 pt-4 sm:grid-cols-[.72fr_1.28fr]">
                <div className="space-y-3">
                  <div className="rounded-2xl bg-white/[.06] p-4"><p className="text-xs font-medium text-slate-400">Nivel de madurez</p><div className="mt-3 flex items-end gap-2"><strong className="text-4xl">68</strong><span className="mb-1 text-xs text-slate-400">/ 100</span></div><div className="mt-4 h-1.5 overflow-hidden rounded-full bg-white/10"><div className="h-full w-[68%] rounded-full bg-cyan-400" /></div><p className="mt-3 text-xs font-semibold text-cyan-300">+12% este trimestre</p></div>
                  <div className="rounded-2xl bg-white/[.06] p-4"><p className="text-xs font-medium text-slate-400">Activos monitoreados</p><p className="mt-2 text-2xl font-bold">24</p><p className="mt-1 text-[11px] text-slate-400">3 requieren atención</p></div>
                </div>
                <div className="rounded-2xl bg-white/[.06] p-4">
                  <div className="flex items-center justify-between"><p className="text-xs font-medium text-slate-300">Panorama de riesgos</p><span className="rounded-full bg-emerald-400/10 px-2 py-1 text-[10px] font-bold text-emerald-300">ACTUALIZADO</span></div>
                  <div className="risk-chart mt-7 flex h-32 items-end justify-between gap-3" role="img" aria-label="Gráfica ilustrativa de riesgos">{[38, 68, 46, 82, 58, 72, 43].map((height, index) => <span key={index} className="w-full rounded-t bg-cyan-400/80" style={{ height: `${height}%`, opacity: .45 + index * .07 }} />)}</div>
                  <div className="mt-3 flex justify-between text-[9px] uppercase tracking-wider text-slate-500"><span>Identificar</span><span>Proteger</span><span>Recuperar</span></div>
                  <div className="mt-6 rounded-xl border border-cyan-300/15 bg-cyan-300/[.06] p-3"><div className="flex gap-3"><Bot className="mt-0.5 shrink-0 text-cyan-300" size={18} /><div><p className="text-xs font-bold">Recomendación prioritaria</p><p className="mt-1 text-[11px] leading-5 text-slate-400">Active la autenticación multifactor en las cuentas administrativas.</p></div></div></div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section id="solucion" className="scroll-mt-20 py-20 sm:py-28"><div className="mx-auto max-w-7xl px-5 sm:px-8"><div className="mx-auto max-w-3xl text-center"><p className="section-eyebrow">Una visión completa de su seguridad</p><h2 className="mt-3 text-3xl font-extrabold tracking-tight text-[#082443] sm:text-5xl">Todo lo que necesita para pasar de reaccionar a prevenir</h2><p className="mt-5 text-lg leading-8 text-slate-600">Información técnica convertida en decisiones comprensibles para su negocio.</p></div><div className="mt-14 grid gap-5 md:grid-cols-2 lg:grid-cols-3">{capabilities.map(({ icon: Icon, title, description }) => <article className="feature-card rounded-2xl border border-slate-200 bg-white p-6" key={title}><span className="grid size-11 place-items-center rounded-xl bg-cyan-50 text-cyan-700"><Icon size={23} aria-hidden="true" /></span><h3 className="mt-5 text-lg font-bold text-[#082443]">{title}</h3><p className="mt-2 leading-7 text-slate-600">{description}</p></article>)}</div></div></section>

      <section id="como-funciona" className="scroll-mt-20 bg-white py-20 sm:py-28"><div className="mx-auto max-w-7xl px-5 sm:px-8"><div className="grid items-center gap-14 lg:grid-cols-2"><div><p className="section-eyebrow">Simple desde el primer día</p><h2 className="mt-3 text-3xl font-extrabold tracking-tight text-[#082443] sm:text-5xl">De la incertidumbre a un plan de acción</h2><p className="mt-5 max-w-xl text-lg leading-8 text-slate-600">No necesita un equipo especializado para comenzar. La plataforma le guía en cada etapa.</p></div><ol className="space-y-4">{[['01', 'Registre lo importante', 'Identifique los activos tecnológicos que sostienen su operación.'], ['02', 'Evalúe su situación', 'Complete un diagnóstico estructurado con base en estándares reconocidos.'], ['03', 'Priorice y mejore', 'Reciba riesgos ordenados, recomendaciones y reportes para actuar con confianza.']].map(([number, title, text]) => <li className="flex gap-5 rounded-2xl border border-slate-200 bg-[#f8fbfd] p-5 transition hover:border-cyan-300" key={number}><span className="grid size-12 shrink-0 place-items-center rounded-xl bg-[#082443] text-sm font-extrabold text-cyan-300">{number}</span><div><h3 className="font-bold text-[#082443]">{title}</h3><p className="mt-1 leading-6 text-slate-600">{text}</p></div></li>)}</ol></div></div></section>

      <section id="beneficios" className="scroll-mt-20 bg-[#071f3b] py-20 text-white sm:py-24"><div className="mx-auto max-w-7xl px-5 text-center sm:px-8"><p className="section-eyebrow text-cyan-300">Seguridad al alcance de su empresa</p><h2 className="mx-auto mt-3 max-w-3xl text-3xl font-extrabold tracking-tight sm:text-5xl">Conozca sus riesgos antes de que se conviertan en incidentes</h2><p className="mx-auto mt-5 max-w-2xl text-lg leading-8 text-slate-300">Centralice la información, defina prioridades y construya una cultura de mejora continua.</p><Link className="mt-9 inline-flex items-center justify-center gap-2 rounded-xl bg-cyan-400 px-7 py-3.5 font-bold text-[#061b35] transition hover:-translate-y-0.5 hover:bg-cyan-300" to="/login">Comenzar ahora <ArrowRight size={18} /></Link></div></section>

      <footer className="border-t border-slate-200 bg-white py-8"><div className="mx-auto flex max-w-7xl flex-col items-center justify-between gap-4 px-5 text-center text-sm text-slate-500 sm:px-8 md:flex-row md:text-left"><div className="flex items-center gap-2 font-bold text-[#082443]"><ShieldCheck className="text-cyan-600" size={20} /> SecureCommerce Advisor</div><p>Gestión preventiva de ciberseguridad para MIPYMES guatemaltecas.</p><p>© 2026 SecureCommerce</p></div></footer>
    </main>
  )
}
