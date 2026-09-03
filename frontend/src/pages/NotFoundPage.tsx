import { Link } from 'react-router-dom'

export function NotFoundPage() {
  return (
    <main className="grid min-h-screen place-content-center bg-slate-50 px-6 text-center">
      <p className="text-sm font-semibold text-blue-700">Error 404</p>
      <h1 className="mt-2 text-3xl font-bold text-blue-950">Página no encontrada</h1>
      <Link className="mt-6 text-blue-700 underline underline-offset-4" to="/">
        Volver al inicio
      </Link>
    </main>
  )
}

