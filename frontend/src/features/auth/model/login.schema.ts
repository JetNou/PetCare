import { z } from "zod";

export const loginSchema = z.object({
  loginOrEmail: z
    .string()
    .trim()
    .min(3, "Логин или email должен содержать минимум 3 символа")
    .max(100, "Логин или email должен содержать максимум 100 символов")
    .refine((value) => {

      const isLogin = /^[a-zA-Z0-9_]+$/.test(value);
      const isEmail = /^\S+@\S+\.\S+$/.test(value);

      return isLogin || isEmail;
    }, "Введите корректный логин или email"),

  password: z
    .string()
    .trim()
    .min(8, "Пароль должен содержать минимум 8 символов")
    .max(128, "Пароль должен содержать максимум 128 символов")
    .regex(
      /^(?=.*[a-zа-яё])(?=.*[A-ZА-ЯЁ])(?=.*\d)(?=.*[!@#$%^&_*])[A-Za-zА-Яа-яёЁ\d!@#$%^&_*]{8,}$/,
      "Пароль должен содержать заглавную и строчную букву, цифру и спецсимвол"
    ),
});

export type LoginFormData = z.infer<typeof loginSchema>;