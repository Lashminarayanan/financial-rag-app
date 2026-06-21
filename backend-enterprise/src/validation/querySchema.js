import { z } from 'zod';

export const querySchema = z.object({
  query: z.string().min(3, 'query must be at least 3 characters'),
  topK: z.number().int().positive().max(10).optional(),
  mode: z.enum(['standard', 'comparative', 'report']).optional()
});
