import { z } from 'zod';

export const restorePetSchema = z.object({
  token: z.string().trim().min(1, 'Введите токен восстановления').max(100, 'Токен не должен превышать 100 символов'),
});

export type RestorePetFormValues = z.infer<typeof restorePetSchema>;
