import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQuery } from "@tanstack/react-query";
import { ArrowLeft, Save } from "lucide-react";
import { useEffect } from "react";
import { useForm } from "react-hook-form";
import { Link, useNavigate, useParams } from "react-router-dom";

import { createAsset, getAsset, updateAsset } from "../api/assets";
import { assetSchema, type AssetFormValues } from "../schemas/assets";

const defaults: AssetFormValues = {
  name: "",
  internal_code: "",
  asset_type: "computer",
  description: "",
  owner: "",
  technical_owner: "",
  location: "",
  ip_address: "",
  operating_system: "",
  manufacturer: "",
  model: "",
  exposure_level: "internal",
  status: "active",
  acquisition_date: "",
  confidentiality_criticality: 3,
  integrity_criticality: 3,
  availability_criticality: 3,
  tags_text: "",
  notes: "",
};

export function AssetFormPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const existing = useQuery({
    queryKey: ["asset", id],
    queryFn: () => getAsset(id!),
    enabled: Boolean(id),
  });
  const {
    register,
    reset,
    handleSubmit,
    formState: { errors },
  } = useForm<AssetFormValues>({
    resolver: zodResolver(assetSchema),
    defaultValues: defaults,
  });
  useEffect(() => {
    if (existing.data)
      reset({
        ...existing.data,
        description: existing.data.description ?? "",
        owner: existing.data.owner ?? "",
        technical_owner: existing.data.technical_owner ?? "",
        location: existing.data.location ?? "",
        ip_address: existing.data.ip_address ?? "",
        operating_system: existing.data.operating_system ?? "",
        manufacturer: existing.data.manufacturer ?? "",
        model: existing.data.model ?? "",
        acquisition_date: existing.data.acquisition_date ?? "",
        tags_text: existing.data.tags.join(", "),
        notes: existing.data.notes ?? "",
      });
  }, [existing.data, reset]);
  const save = useMutation({
    mutationFn: (values: AssetFormValues) =>
      id ? updateAsset(id, values) : createAsset(values),
    onSuccess: () => navigate("/activos"),
  });
  const input =
    "mt-1.5 w-full rounded-lg border border-slate-300 bg-white px-3 py-2.5";
  return (
    <main className="min-h-screen bg-slate-50 px-5 py-8">
      <section className="mx-auto max-w-4xl">
        <Link
          className="inline-flex items-center gap-2 text-sm text-blue-700"
          to="/activos"
        >
          <ArrowLeft size={16} />
          Inventario
        </Link>
        <h1 className="mt-5 text-3xl font-bold text-blue-950">
          {id ? "Editar activo" : "Registrar activo"}
        </h1>
        <p className="mt-2 text-slate-600">
          La criticidad general será el nivel más alto entre confidencialidad,
          integridad y disponibilidad.
        </p>
        <form
          className="mt-7 space-y-7"
          onSubmit={handleSubmit((values) => save.mutate(values))}
        >
          <div className="grid gap-5 rounded-xl border border-slate-200 bg-white p-6 sm:grid-cols-2">
            <label className="text-sm font-medium">
              Nombre
              <input className={input} {...register("name")} />
              {errors.name && (
                <span className="text-sm text-red-700">
                  {errors.name.message}
                </span>
              )}
            </label>
            <label className="text-sm font-medium">
              Código interno
              <input className={input} {...register("internal_code")} />
              {errors.internal_code && (
                <span className="text-sm text-red-700">
                  {errors.internal_code.message}
                </span>
              )}
            </label>
            <label className="text-sm font-medium">
              Tipo
              <select className={input} {...register("asset_type")}>
                <option value="server">Servidor</option>
                <option value="computer">Computadora</option>
                <option value="mobile">Dispositivo móvil</option>
                <option value="network">Equipo de red</option>
                <option value="application">Aplicación</option>
                <option value="database">Base de datos</option>
                <option value="information">Información</option>
                <option value="cloud_service">Servicio en la nube</option>
                <option value="critical_account">Cuenta crítica</option>
                <option value="supplier">Proveedor</option>
                <option value="other">Otro</option>
              </select>
            </label>
            <label className="text-sm font-medium">
              Estado
              <select className={input} {...register("status")}>
                <option value="active">Activo</option>
                <option value="inactive">Inactivo</option>
                <option value="maintenance">Mantenimiento</option>
                <option value="retired">Retirado</option>
              </select>
            </label>
            <label className="text-sm font-medium">
              Propietario
              <input className={input} {...register("owner")} />
            </label>
            <label className="text-sm font-medium">
              Responsable técnico
              <input className={input} {...register("technical_owner")} />
            </label>
            <label className="text-sm font-medium">
              Ubicación
              <input className={input} {...register("location")} />
            </label>
            <label className="text-sm font-medium">
              Dirección IP
              <input
                className={input}
                placeholder="192.0.2.10"
                {...register("ip_address")}
              />
              {errors.ip_address && (
                <span className="text-sm text-red-700">
                  Dirección IP inválida
                </span>
              )}
            </label>
            <label className="text-sm font-medium">
              Sistema operativo
              <input className={input} {...register("operating_system")} />
            </label>
            <label className="text-sm font-medium">
              Fabricante
              <input className={input} {...register("manufacturer")} />
            </label>
            <label className="text-sm font-medium">
              Modelo
              <input className={input} {...register("model")} />
            </label>
            <label className="text-sm font-medium">
              Exposición
              <select className={input} {...register("exposure_level")}>
                <option value="internal">Interno</option>
                <option value="limited">Acceso limitado</option>
                <option value="public">Público en Internet</option>
              </select>
            </label>
            <label className="text-sm font-medium">
              Fecha de adquisición
              <input
                className={input}
                type="date"
                {...register("acquisition_date")}
              />
            </label>
            <label className="text-sm font-medium">
              Etiquetas, separadas por coma
              <input className={input} {...register("tags_text")} />
            </label>
            <label className="text-sm font-medium sm:col-span-2">
              Descripción
              <textarea
                className={input}
                rows={3}
                {...register("description")}
              />
            </label>
          </div>
          <fieldset className="rounded-xl border border-slate-200 bg-white p-6">
            <legend className="px-2 font-semibold text-blue-950">
              Criticidad: 1 baja, 5 crítica
            </legend>
            <div className="grid gap-5 sm:grid-cols-3">
              {(
                [
                  "confidentiality_criticality",
                  "integrity_criticality",
                  "availability_criticality",
                ] as const
              ).map((field, index) => (
                <label key={field} className="text-sm font-medium">
                  {["Confidencialidad", "Integridad", "Disponibilidad"][index]}
                  <select className={input} {...register(field, { valueAsNumber: true })}>
                    {[1, 2, 3, 4, 5].map((level) => (
                      <option key={level} value={level}>
                        {level}
                      </option>
                    ))}
                  </select>
                </label>
              ))}
            </div>
          </fieldset>
          <label className="block text-sm font-medium">
            Observaciones
            <textarea className={input} rows={3} {...register("notes")} />
          </label>
          {save.isError && (
            <p role="alert" className="rounded-lg bg-red-50 p-3 text-red-800">
              No fue posible guardar. Revise los datos o el código interno.
            </p>
          )}
          <button
            className="inline-flex items-center gap-2 rounded-lg bg-blue-950 px-5 py-3 font-semibold text-white disabled:opacity-60"
            disabled={save.isPending}
            type="submit"
          >
            <Save size={18} />
            {save.isPending ? "Guardando…" : "Guardar activo"}
          </button>
        </form>
      </section>
    </main>
  );
}
