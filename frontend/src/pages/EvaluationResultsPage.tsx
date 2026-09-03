import { useQuery } from "@tanstack/react-query";
import { ArrowLeft } from "lucide-react";
import { Link, useParams } from "react-router-dom";
import { getResults } from "../api/evaluations";

export function EvaluationResultsPage() {
  const { id = "" } = useParams();
  const results = useQuery({
    queryKey: ["evaluation-results", id],
    queryFn: () => getResults(id),
  });
  return (
    <main className="min-h-screen bg-slate-50 px-5 py-8">
      <section className="mx-auto max-w-5xl">
        <Link
          className="inline-flex items-center gap-2 text-sm text-blue-700"
          to="/evaluaciones"
        >
          <ArrowLeft size={16} />
          Evaluaciones
        </Link>
        <h1 className="mt-5 text-3xl font-bold text-blue-950">
          Resultados NIST CSF 2.0
        </h1>
        {results.isPending && <p className="mt-8">Calculando resultados…</p>}
        {results.isError && (
          <p className="mt-8 text-red-800" role="alert">
            No fue posible calcular los resultados.
          </p>
        )}
        {results.data && (
          <>
            <div className="mt-7 grid gap-4 sm:grid-cols-3">
              <div className="rounded-xl border bg-white p-5">
                <p className="text-sm text-slate-600">Perfil actual</p>
                <p className="mt-2 text-3xl font-bold text-blue-950">
                  {results.data.current_profile}%
                </p>
              </div>
              <div className="rounded-xl border bg-white p-5">
                <p className="text-sm text-slate-600">Perfil objetivo</p>
                <p className="mt-2 text-3xl font-bold text-blue-950">
                  {results.data.target_profile}%
                </p>
              </div>
              <div className="rounded-xl border bg-white p-5">
                <p className="text-sm text-slate-600">Brecha</p>
                <p className="mt-2 text-3xl font-bold text-blue-950">
                  {results.data.gap}%
                </p>
              </div>
            </div>
            <h2 className="mt-9 text-xl font-bold text-blue-950">
              Resultado por función
            </h2>
            <div className="mt-4 space-y-4">
              {results.data.by_function.map((item) => (
                <div key={item.code} className="rounded-xl border bg-white p-5">
                  <div className="flex justify-between gap-4">
                    <p className="font-semibold">{item.name}</p>
                    <p>
                      {item.score}% · {item.answered}/{item.total} respuestas
                    </p>
                  </div>
                  <div
                    className="mt-3 h-3 overflow-hidden rounded-full bg-slate-200"
                    role="progressbar"
                    aria-label={item.name}
                    aria-valuenow={item.score}
                    aria-valuemin={0}
                    aria-valuemax={100}
                  >
                    <div
                      className="h-full bg-blue-700"
                      style={{ width: `${item.score}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </>
        )}
      </section>
    </main>
  );
}
