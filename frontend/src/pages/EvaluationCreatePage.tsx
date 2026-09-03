import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQuery } from "@tanstack/react-query";
import { ArrowLeft, Save } from "lucide-react";
import { useEffect } from "react";
import { useForm } from "react-hook-form";
import { Link, useNavigate } from "react-router-dom";
import { getAssets } from "../api/assets";
import { createEvaluation, getFrameworks } from "../api/evaluations";
import {
  evaluationSchema,
  type EvaluationFormValues,
} from "../schemas/evaluations";

export function EvaluationCreatePage() {
  const navigate = useNavigate();
  const frameworks = useQuery({
    queryKey: ["frameworks"],
    queryFn: getFrameworks,
  });
  const assets = useQuery({
    queryKey: ["assets", "evaluation"],
    queryFn: () => getAssets(),
  });
  const {
    register,
    setValue,
    handleSubmit,
    formState: { errors },
  } = useForm<EvaluationFormValues>({
    resolver: zodResolver(evaluationSchema),
    defaultValues: {
      code: "",
      name: "",
      scope: "",
      target_maturity: 3,
      framework_id: "",
      asset_ids: [],
    },
  });
  useEffect(() => {
    if (frameworks.data?.[0]) setValue("framework_id", frameworks.data[0].id);
  }, [frameworks.data, setValue]);
  const create = useMutation({
    mutationFn: createEvaluation,
    onSuccess: (item) => navigate(`/evaluaciones/${item.id}/cuestionario`),
  });
  const input = "mt-1.5 w-full rounded-lg border border-slate-300 px-3 py-2.5";
  return (
    <main className="min-h-screen bg-slate-50 px-5 py-8">
      <form
        className="mx-auto max-w-3xl"
        onSubmit={handleSubmit((values) => create.mutate(values))}
      >
        <Link
          className="inline-flex items-center gap-2 text-sm text-blue-700"
          to="/evaluaciones"
        >
          <ArrowLeft size={16} />
          Evaluaciones
        </Link>
        <h1 className="mt-5 text-3xl font-bold text-blue-950">
          Nueva evaluación
        </h1>
        <div className="mt-7 grid gap-5 rounded-xl border border-slate-200 bg-white p-6 sm:grid-cols-2">
          <label className="text-sm font-medium">
            Código
            <input className={input} {...register("code")} />
            {errors.code && (
              <span className="text-sm text-red-700">
                {errors.code.message}
              </span>
            )}
          </label>
          <label className="text-sm font-medium">
            Nombre
            <input className={input} {...register("name")} />
          </label>
          <label className="text-sm font-medium sm:col-span-2">
            Alcance
            <textarea className={input} rows={3} {...register("scope")} />
            {errors.scope && (
              <span className="text-sm text-red-700">
                {errors.scope.message}
              </span>
            )}
          </label>
          <label className="text-sm font-medium">
            Marco
            <select className={input} {...register("framework_id")}>
              {frameworks.data?.map((framework) => (
                <option key={framework.id} value={framework.id}>
                  {framework.name} {framework.version}
                </option>
              ))}
            </select>
          </label>
          <label className="text-sm font-medium">
            Perfil objetivo
            <select
              className={input}
              {...register("target_maturity", { valueAsNumber: true })}
            >
              {[0, 1, 2, 3, 4].map((value) => (
                <option key={value} value={value}>
                  {value}
                </option>
              ))}
            </select>
          </label>
          <fieldset className="sm:col-span-2">
            <legend className="font-semibold text-blue-950">
              Activos incluidos
            </legend>
            <div className="mt-3 grid gap-2 sm:grid-cols-2">
              {assets.data?.items.map((asset) => (
                <label
                  key={asset.id}
                  className="flex gap-2 rounded-lg border border-slate-200 p-3"
                >
                  <input
                    type="checkbox"
                    value={asset.id}
                    {...register("asset_ids")}
                  />
                  <span>{asset.name}</span>
                </label>
              ))}
            </div>
          </fieldset>
        </div>
        {create.isError && (
          <p className="mt-5 text-red-800" role="alert">
            No fue posible crear la evaluación.
          </p>
        )}
        <button
          className="mt-6 inline-flex items-center gap-2 rounded-lg bg-blue-950 px-5 py-3 font-semibold text-white"
          type="submit"
        >
          <Save size={18} />
          Crear y responder
        </button>
      </form>
    </main>
  );
}
