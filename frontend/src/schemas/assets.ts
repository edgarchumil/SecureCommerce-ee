import { z } from 'zod'

const optionalText = z.string().max(4000).optional()

export const assetSchema = z.object({
  name: z.string().min(2, 'Ingrese un nombre').max(180),
  internal_code: z.string().min(1, 'Ingrese un código').max(80).regex(/^[A-Za-z0-9._-]+$/, 'Use letras, números, punto, guion o guion bajo'),
  asset_type: z.enum(['server', 'computer', 'mobile', 'network', 'application', 'database', 'information', 'cloud_service', 'critical_account', 'supplier', 'other']),
  description: optionalText,
  owner: z.string().max(160).optional(),
  technical_owner: z.string().max(160).optional(),
  location: z.string().max(180).optional(),
  ip_address: z.union([z.literal(''), z.ipv4(), z.ipv6()]).optional(),
  operating_system: z.string().max(120).optional(),
  manufacturer: z.string().max(120).optional(),
  model: z.string().max(120).optional(),
  exposure_level: z.enum(['internal', 'limited', 'public']),
  status: z.enum(['active', 'inactive', 'maintenance', 'retired']),
  acquisition_date: z.string().optional(),
  confidentiality_criticality: z.number().int().min(1).max(5),
  integrity_criticality: z.number().int().min(1).max(5),
  availability_criticality: z.number().int().min(1).max(5),
  tags_text: z.string().optional(),
  notes: optionalText,
})

export type AssetFormValues = z.infer<typeof assetSchema>
