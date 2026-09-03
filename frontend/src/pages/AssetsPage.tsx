import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, Pencil, Plus, Search, Trash2 } from "lucide-react";
import { useState } from "react";
import { Link } from "react-router-dom";

import { deleteAsset, getAssets } from "../api/assets";

const TYPE_LABELS: Record<string, string> = {
  server: "Servidor",
  computer: "Computadora",
  mobile: "Dispositivo móvil",
  network: "Equipo de red",
  application: "Aplicación",
  database: "Base de datos",
  information: "Información",
  cloud_service: "Servicio en la nube",
  critical_account: "Cuenta crítica",
  supplier: "Proveedor",
  other: "Otro",
};
const STATUS_LABELS: Record<string, string> = {
  active: "Activo",
  inactive: "Inactivo",
  maintenance: "Mantenimiento",
  retired: "Retirado",
};

export function AssetsPage() {
  const [search, setSearch] = useState("");
  const queryClient = useQueryClient();
  const assets = useQuery({
    queryKey: ["assets", search],
    queryFn: () => getAssets(search),
  });
  const remove = useMutation({
    mutationFn: deleteAsset,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["assets"] }),
  });
  const confirmDelete = (id: string, name: string) => {
    if (window.confirm(`¿Retirar “${name}” del inventario?`)) remove.mutate(id);
  };
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
            <p className="text-sm font-semibold text-blue-700">
              Inventario centralizado
            </p>
            <h1 className="mt-1 text-3xl font-bold text-blue-950">
              Activos tecnológicos
            </h1>
            <p className="mt-2 text-slate-600">
              Registre lo que su empresa necesita proteger.
            </p>
          </div>
          <Link
            className="inline-flex items-center justify-center gap-2 rounded-lg bg-blue-950 px-4 py-3 font-semibold text-white"
            to="/activos/nuevo"
          >
            <Plus size={18} />
            Registrar activo
          </Link>
        </div>
        <label className="relative mt-7 block max-w-md">
          <span className="sr-only">Buscar activos</span>
          <Search className="absolute left-3 top-3 text-slate-500" size={18} />
          <input
            className="w-full rounded-lg border border-slate-300 bg-white py-2.5 pl-10 pr-3"
            placeholder="Buscar por nombre o código"
            value={search}
            onChange={(event) => setSearch(event.target.value)}
          />
        </label>
        {assets.isPending && <p className="mt-8">Cargando inventario…</p>}
        {assets.isError && (
          <p role="alert" className="mt-8 text-red-800">
            No fue posible cargar el inventario.
          </p>
        )}
        {assets.data?.items.length === 0 && (
          <div className="mt-8 rounded-xl border border-dashed border-slate-300 bg-white p-10 text-center">
            <p className="font-semibold text-blue-950">Aún no hay activos</p>
            <p className="mt-2 text-slate-600">
              Registre el primer equipo, servicio o información importante.
            </p>
          </div>
        )}
        {assets.data && assets.data.items.length > 0 && (
          <div className="mt-7 overflow-x-auto rounded-xl border border-slate-200 bg-white">
            <table className="w-full text-left text-sm">
              <thead className="bg-slate-100 text-slate-700">
                <tr>
                  <th className="px-4 py-3">Activo</th>
                  <th className="px-4 py-3">Tipo</th>
                  <th className="px-4 py-3">Estado</th>
                  <th className="px-4 py-3">Criticidad</th>
                  <th className="px-4 py-3">
                    <span className="sr-only">Acciones</span>
                  </th>
                </tr>
              </thead>
              <tbody>
                {assets.data.items.map((asset) => (
                  <tr key={asset.id} className="border-t border-slate-200">
                    <td className="px-4 py-3">
                      <p className="font-semibold text-slate-900">
                        {asset.name}
                      </p>
                      <p className="text-slate-500">{asset.internal_code}</p>
                    </td>
                    <td className="px-4 py-3">
                      {TYPE_LABELS[asset.asset_type]}
                    </td>
                    <td className="px-4 py-3">{STATUS_LABELS[asset.status]}</td>
                    <td className="px-4 py-3">
                      <span className="rounded-full bg-sky-100 px-2 py-1 font-semibold text-blue-950">
                        Nivel {asset.overall_criticality} de 5
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex justify-end gap-2">
                        <Link
                          aria-label={`Editar ${asset.name}`}
                          className="rounded-md p-2 text-blue-700 hover:bg-blue-50"
                          to={`/activos/${asset.id}/editar`}
                        >
                          <Pencil size={17} />
                        </Link>
                        <button
                          aria-label={`Eliminar ${asset.name}`}
                          className="rounded-md p-2 text-red-700 hover:bg-red-50"
                          onClick={() => confirmDelete(asset.id, asset.name)}
                        >
                          <Trash2 size={17} />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </main>
  );
}
