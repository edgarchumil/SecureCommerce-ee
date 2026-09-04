import { z } from 'zod'

export const loginSchema = z.object({
  email: z.string().email('Ingrese un correo válido'),
  password: z.string().min(1, 'Ingrese su contraseña'),
  mfa_code: z.string().regex(/^\d{6}$/, 'Ingrese los 6 dígitos').optional().or(z.literal('')),
  organization_id: z.string().uuid().optional(),
})

export type LoginValues = z.infer<typeof loginSchema>

export const normalizeOrganizationSlug = (value: string) => value
  .trim()
  .toLowerCase()
  .replace(/^https?:\/\//, '')
  .replace(/^www\./, '')
  .normalize('NFD')
  .replace(/[\u0300-\u036f]/g, '')
  .replace(/[^a-z0-9]+/g, '-')
  .replace(/^-+|-+$/g, '')

export const registerSchema = z.object({
  full_name: z.string().min(2, 'Ingrese su nombre'),
  email: z.string().email('Ingrese un correo válido'),
  password: z.string().min(12, 'Use al menos 12 caracteres'),
  organization_name: z.string().min(2, 'Ingrese el nombre de la empresa'),
  organization_slug: z.string()
    .transform(normalizeOrganizationSlug)
    .pipe(z.string().regex(/^[a-z0-9]+(?:-[a-z0-9]+)*$/, 'Ingrese un nombre o sitio web válido')),
  sector: z.string().optional(), size: z.string().optional(),
  country: z.string().length(2, 'Use un código de dos letras'),
})
export type RegisterValues = z.infer<typeof registerSchema>
