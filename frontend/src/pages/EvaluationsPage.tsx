import { useQuery } from "@tanstack/react-query";
import { ArrowLeft, ClipboardCheck, Plus } from "lucide-react";
import { Link } from "react-router-dom";
import { getEvaluations } from "../api/evaluations";

const STATUS: Record<string, string> = {
  draft: "Borrador",
  in_review: "En revisión",
  approved: "Aprobada",
  closed: "Cerrada",
};
export function EvaluationsPage() {
  const evaluations = useQuery({
    queryKey: ["evaluations"],
    queryFn: getEvaluations,
  });
  return (
    <main className="min-h-screen bg-slate-50 px-5 py-8">
      <section className="mx-auto max-w-6xl">
        <Link
          className="inline-flex items-center gap-2 text-sm text-blue-700"
          to="/panel"
        >
          <ArrowLeft size={16} />
          Panel
        </Link>
        <div className="mt-5 flex flex-col justify-between gap-4 sm:flex-row sm:items-end">
          <div>
            <p className="text-sm font-semibold text-blue-700">NIST CSF 2.0</p>
            <h1 className="mt-1 text-3xl font-bold text-blue-950">
              Evaluaciones
            </h1>
            <p className="mt-2 text-slate-600">
              Conozca qué prácticas están implementadas y cuáles conviene
              priorizar.
            </p>
          </div>
          <Link
            className="inline-flex items-center justify-center gap-2 rounded-lg bg-blue-950 px-4 py-3 font-semibold text-white"
            to="/evaluaciones/nueva"
          >
            <Plus size={18} />
            Nueva evaluación
          </Link>
        </div>
        {evaluations.isPending && (
          <p className="mt-8">Cargando evaluaciones…</p>
        )}
        {evaluations.isError && (
          <p className="mt-8 text-red-800" role="alert">
            No fue posible cargar las evaluaciones.
          </p>
        )}
        {evaluations.data?.length === 0 && (
          <div className="mt-8 rounded-xl border border-dashed border-slate-300 bg-white p-10 text-center">
            <ClipboardCheck className="mx-auto text-blue-700" />
            <p className="mt-3 font-semibold">Aún no hay evaluaciones</p>
          </div>
        )}
        <div className="mt-7 grid gap-4">
          {evaluations.data?.map((item) => (
            <article
              key={item.id}
              className="rounded-xl border border-slate-200 bg-white p-5"
            >
              <div className="flex flex-wrap justify-between gap-3">
                <div>
                  <h2 className="font-semibold text-blue-950">{item.name}</h2>
                  <p className="mt-1 text-sm text-slate-600">
                    {item.code} · Versión {item.version} · {STATUS[item.status]}
                  </p>
                </div>
                <div className="flex gap-3">
                  <Link
                    className="font-semibold text-blue-700"
                    to={`/evaluaciones/${item.id}/cuestionario`}
                  >
                    Cuestionario
                  </Link>
                  <Link
                    className="font-semibold text-blue-700"
                    to={`/evaluaciones/${item.id}/resultados`}
                  >
                    Resultados
                  </Link>
                </div>
              </div>
            </article>
          ))}
        </div>
      </section>
    </main>
  );
}
