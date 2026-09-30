import { z } from 'zod';

export const petCreateSchema = z
  .object({
    name: z
    .string()
    .trim()
    .min(1, 'Укажите кличку питомца')
    .max(100, 'Кличка питомца не должна превышать 100 символов')
    .regex(/^[a-zA-Zа-яА-ЯёЁ\s-]+$/, 'Кличка может содержать только буквы, пробелы и дефис'),

    gender: z
    .string()
    .trim()
    .min(1, 'Выберите пол питомца')
    .max(20, 'Пол питомца не должен превышать 20 символов')
    .regex(/^[a-zA-Zа-яА-ЯёЁ\s-]+$/, 'Пол может содержать только буквы, пробелы и дефис'),

    date_birth: z
      .string()
      .trim()
      .min(1, 'Укажите дату рождения питомца')
      .refine((val) => /^\d{4}-\d{2}-\d{2}$/.test(val), {
        message: 'Формат: YYYY-MM-DD (например, 2026-04-01)',
      })
      .refine((val) => {
        const [year, month, day] = val.split('-').map(Number);
        const birthDate = new Date(year, month - 1, day);

        const now = new Date();
        const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());

        return birthDate <= today;
      }, {
        message: 'Дата рождения не может быть позже сегодняшнего дня',
      })
      .refine((val) => {
        const birthDate = new Date(val);
        const now = new Date();
        const minDate = new Date(now.getFullYear() - 150, now.getMonth(), now.getDate());
        return birthDate >= minDate;
      }, {
        message: 'Дата рождения не может быть старше 150 лет от сегодня',
      })
      .optional()
      .or(z.literal('')),
    weight: z.number({ message: 'Вес должен быть числом' }).positive('Вес питомца должен быть больше 0').max(1000, "Вес не должен быть больше 1000 кг").or(z.literal('')),
    breed: z.string().max(100, 'Порода не должна превышать 100 символов').regex(/^[a-zA-Zа-яА-ЯёЁ\s-]+$/,'Порода может содержать только буквы, пробелы и дефис').optional().or(z.literal('')),
    color: z.string().max(50, 'Окрас не должен превышать 50 символов').regex(/^[a-zA-Zа-яА-ЯёЁ\s-]+$/,'Окрас может содержать только буквы, пробелы и дефис').optional().or(z.literal('')),
    chip: z.string().trim().regex(/^[A-Z0-9]*$/, 'Чип должен содержать только цифры и заглавные латинские буквы').min(15, 'Чип должен содержать минимум 15 символов').max(18, 'Чип должен содержать максимум 18 символов').optional().or(z.literal('')),
  })

export type PetCreateFormValues = z.infer<typeof petCreateSchema>;
