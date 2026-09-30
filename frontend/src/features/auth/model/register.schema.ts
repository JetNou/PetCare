import { z } from "zod";

export const registerSchema = z
  .object({
    login: z
      .string()
      .trim()
      .min(3, "Логин должен содержать минимум 3 символа")
      .max(50, "Логин должен содержать максимум 50 символов")
      .regex(/^[a-zA-Z0-9_]+$/, "Логин может содержать только латинские буквы, цифры и _"),

    full_name: z
      .string()
      .trim()
      .min(2, "Имя должно содержать минимум 2 символа")
      .max(100, "Имя должно содержать максимум 100 символов")
      .regex(
        /^[a-zA-Zа-яА-ЯёЁ\s\-]+$/,
        "Имя может содержать только буквы, пробелы и дефис"
      ),

    email: z
      .string()
      .trim()
      .min(3, "Email должен содержать минимум 3 символа")
      .max(100, "Email должен содержать максимум 100 символов")
      .email("Введите корректный email"),

    password: z
      .string()
      .trim()
      .min(8, "Пароль должен содержать минимум 8 символов")
      .max(128, "Пароль должен содержать максимум 128 символов")
      .regex(
        /^(?=.*[a-zа-яё])(?=.*[A-ZА-ЯЁ])(?=.*\d)(?=.*[!@#$%^&*])[A-Za-zА-Яа-яёЁ\d!@#$%^&*]{8,}$/,
        "Пароль должен содержать заглавную и строчную букву, цифру и спецсимвол"
      ),

    confirm_password: z
      .string()
      .trim()
      .min(1, "Подтвердите пароль"),

    agreement: z.literal(true, {
      message: "Необходимо согласие с политикой конфиденциальности",
    }),
  })
  .refine((data) => data.password === data.confirm_password, {
    message: "Пароли не совпадают",
    path: ["confirm_password"],
  });

export type RegisterFormData = z.infer<typeof registerSchema>;