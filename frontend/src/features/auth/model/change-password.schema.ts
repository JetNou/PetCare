import { z } from 'zod';

export const changePasswordSchema = z.object({
  token: z
    .string()
    .trim()
    .min(1, "Вставьте код подтверждения из письма"),

  new_password: z
    .string()
    .min(8, "Пароль должен содержать минимум 8 символов")
    .max(128, "Пароль должен содержать максимум 128 символов")
    .regex(
      /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/,
      "Пароль должен содержать заглавные, строчные буквы и цифры"
    ),
});

export type ChangePasswordFormData = z.infer<typeof changePasswordSchema>;
