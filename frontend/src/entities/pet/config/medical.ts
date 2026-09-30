import { TypeAction, MedicalHistoryStatus } from '../model/types';

export const TYPE_ACTION_OPTIONS: {
  value: (typeof TypeAction)[keyof typeof TypeAction];
  label: string;
}[] = [
  { value: TypeAction.Inspection, label: 'Осмотр' },
  { value: TypeAction.Tests, label: 'Анализы' },
  { value: TypeAction.Diagnostics, label: 'Диагностика' },
  { value: TypeAction.Complex, label: 'Комплекс' },
  { value: TypeAction.ParasiteTreatment, label: 'Паразиты' },
  { value: TypeAction.Surgery, label: 'Хирургия' },
  { value: TypeAction.TreatmentCourse, label: 'Курс лечения' },
  { value: TypeAction.Dentistry, label: 'Стоматология' },
  { value: TypeAction.Grooming, label: 'Груминг' },
  { value: TypeAction.Other, label: 'Другое' },
];

export function typeActionLabel(value: string | null | undefined): string {
  const row = TYPE_ACTION_OPTIONS.find((o) => o.value === value);
  return row?.label ?? value ?? '—';
}

export const MEDICAL_STATUS_OPTIONS: {
  value: (typeof MedicalHistoryStatus)[keyof typeof MedicalHistoryStatus];
  label: string;
}[] = [
  { value: MedicalHistoryStatus.Planned, label: 'Запланировано' },
  { value: MedicalHistoryStatus.Completed, label: 'Завершено' },
  { value: MedicalHistoryStatus.Overdue, label: 'Просрочено' },
];
