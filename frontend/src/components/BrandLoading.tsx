import { ShieldCheck } from 'lucide-react'

export function BrandLoading({ message = 'Expertos en la seguridad TI' }: { message?: string }) {
  return <div role="status" aria-live="polite" aria-label="Cargando SecureCommerce Advisor" className="fixed inset-0 z-[100] grid min-h-screen place-items-center overflow-hidden bg-[#061b35] px-6 text-white">
    <div aria-hidden="true" className="absolute h-80 w-80 rounded-full bg-cyan-400/10 blur-3xl" />
    <div className="relative flex flex-col items-center text-center">
      <div className="relative mb-8 grid h-28 w-28 place-items-center">
        <span aria-hidden="true" className="absolute inset-0 rounded-full border border-cyan-300/15" />
        <span aria-hidden="true" className="absolute inset-0 animate-spin rounded-full border-2 border-transparent border-r-cyan-300/30 border-t-cyan-300 motion-reduce:animate-none" />
        <span className="grid h-20 w-20 place-items-center rounded-3xl bg-cyan-400 text-[#061b35] shadow-[0_0_45px_rgba(34,211,238,.2)]"><ShieldCheck size={46} strokeWidth={1.8} aria-hidden="true" /></span>
      </div>
      <p className="text-3xl font-bold tracking-tight sm:text-4xl">SecureCommerce</p>
      <p className="mt-2 text-xs font-semibold uppercase tracking-[0.4em] text-cyan-300">Advisor</p>
      <p className="mt-8 text-sm text-slate-300">{message}</p>
      <span aria-hidden="true" className="mt-5 h-1 w-24 animate-pulse rounded-full bg-cyan-300 motion-reduce:animate-none" />
    </div>
  </div>
}
