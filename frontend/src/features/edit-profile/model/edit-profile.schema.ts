import { z } from 'zod';

export const editProfileSchema = z.object({
  user_login: z
      .string()
      .trim()
      .min(3, "Логин должен содержать минимум 3 символа")
      .max(50, "Логин должен содержать максимум 50 символов")
      .regex(/^[a-zA-Z0-9_]+$/, "Логин может содержать только латинские буквы, цифры и _"),

  user_full_name: z
      .string()
      .trim()
      .min(2, "Имя должно содержать минимум 2 символа")
      .max(100, "Имя должно содержать максимум 100 символов")
      .regex(
        /^[a-zA-Zа-яА-ЯёЁ\s\-]+$/,
        "Имя может содержать только буквы, пробелы и дефис"
      ),

  user_email: z
        .string()
        .trim()
        .min(3, "Email должен содержать минимум 3 символа")
        .max(100, "Email должен содержать максимум 100 символов")
        .email("Введите корректный email"),
});

export type EditProfileFormData = z.infer<typeof editProfileSchema>;
