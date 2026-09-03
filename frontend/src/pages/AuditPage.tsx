import { useQuery } from '@tanstack/react-query'
import { getAudit } from '../api/administration'
import { Page } from './OrganizationPage'
export function AuditPage(){const query=useQuery({queryKey:['audit'],queryFn:getAudit});return <Page title="Historial de auditoría" description="Últimas 100 acciones registradas para su organización."><div className="overflow-x-auto rounded-xl border bg-white"><table className="w-full text-left text-sm"><thead><tr><th className="p-3">Fecha</th><th>Acción</th><th>Recurso</th><th>Resultado</th></tr></thead><tbody>{query.data?.map(item=><tr key={item.id} className="border-t"><td className="p-3">{new Date(item.created_at).toLocaleString()}</td><td>{item.action}</td><td>{item.resource_type}</td><td>{item.result}</td></tr>)}</tbody></table></div></Page>}
