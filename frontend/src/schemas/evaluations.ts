import { z } from 'zod'

export const evaluationSchema = z.object({
  code: z.string().min(1, 'Ingrese un código').max(80).regex(/^[A-Za-z0-9._-]+$/),
  name: z.string().min(2, 'Ingrese un nombre').max(180),
  scope: z.string().min(5, 'Describa brevemente el alcance').max(4000),
  target_maturity: z.number().int().min(0).max(4),
  framework_id: z.string().uuid('Seleccione un marco'),
  asset_ids: z.array(z.string().uuid()).max(200),
})
export type EvaluationFormValues = z.infer<typeof evaluationSchema>

