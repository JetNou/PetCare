import { forwardRef, useEffect } from 'react';
import {Controller, useForm} from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Input } from '@shared/ui/Input.tsx';
import { Button } from '@shared/ui/Button.tsx';
import {
  petsApi,
  TypeAction,
  MedicalHistoryStatus,
  TYPE_ACTION_OPTIONS,
  MEDICAL_STATUS_OPTIONS,
  type MedicalEventResponse,
  type TypeActionValue,
  type MedicalHistoryStatusValue,
} from '@entities/pet';
import { getApiErrorMessage } from '@shared/lib/apiError';
import {Select} from "@shared/ui/Select.tsx";

const schema = z.object({
  type_action: z.string().min(1, 'Выберите тип медицинского события'),
  date: z.string().min(1, 'Укажите дату и время события').refine((val) => /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}$/.test(val), {
    message: 'Формат: YYYY-MM-DD HH:mm',
  }).refine((val) => {
    const inputDate = new Date(val + ':00');
    const now = new Date();
    const minDate = new Date(now.getFullYear() - 150, now.getMonth(), now.getDate());
    return inputDate >= minDate;
  }, {
    message: 'Дата не может быть старше 150 лет',
  }),
  description: z.string().max(1000, 'Описание не должно превышать 1000 символов').optional(),
  notes: z.string().max(500, 'Заметки не должны превышать 500 символов').optional(),
  status: z.string().optional(),
  interval_period: z.number({ message: 'Интервал должен быть числом' }).min(0, 'Интервал не может быть отрицательным').max(730, 'Интервал не должен быть больше 730 дней').optional(),
})

export type MedicalEventFormData = z.infer<typeof schema>;

interface MedicalEventModalProps {
  petId: number;
  event?: MedicalEventResponse | null;
  closeModal: () => void;
  onSaved: () => void;
}

function toDatetimeLocal(iso: string): string {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return '';

  return d.toISOString().slice(0, 16);
}

function fromDatetimeLocal(local: string): string {
  const d = new Date(local);
  return d.toISOString();
}

export const MedicalEventModal = forwardRef<HTMLDivElement, MedicalEventModalProps>(
  ({ petId, event, closeModal, onSaved }, ref) => {
    const isEdit = Boolean(event);
    const {
      register,
      handleSubmit,
      control,
      reset,
      formState: { errors, isSubmitting },
      setError,
    } = useForm<MedicalEventFormData>({
      resolver: zodResolver(schema),
      defaultValues: {
        type_action: TypeAction.Inspection,
        date: '',
        description: '',
        notes: '',
        status: MedicalHistoryStatus.Planned,
        interval_period: 0,
      },
    });

    useEffect(() => {
      if (event) {
        reset({
          type_action: event.type_action ?? TypeAction.Inspection,
          date: toDatetimeLocal(event.date),
          description: event.description ?? '',
          notes: event.notes ?? '',
          status: event.status,
          interval_period: event.interval_period ?? 0,
        });
      } else {
        reset({
          type_action: TypeAction.Inspection,
          date: toDatetimeLocal(new Date().toISOString()),
          description: '',
          notes: '',
          status: MedicalHistoryStatus.Planned,
          interval_period: 0,
        });
      }
    }, [event, reset]);

    const submit = async (data: MedicalEventFormData) => {
      try {
        const isoDate = fromDatetimeLocal(data.date);
        if (isEdit && event) {
          await petsApi.updateMedicalEvent(petId, event.medical_action_id, {
            type_action: data.type_action as TypeActionValue,
            date: isoDate,
            description: data.description || null,
            notes: data.notes || null,
            status: (data.status as MedicalHistoryStatusValue) || null,
            interval_period: data.interval_period ?? null,
          });
        } else {
          await petsApi.createMedicalEvent(petId, {
            type_action: data.type_action as TypeActionValue,
            date: isoDate,
            description: data.description || null,
            notes: data.notes || null,
            status: (data.status as MedicalHistoryStatusValue) || undefined,
            interval_period: data.interval_period ?? 0,
          });
        }
        onSaved();
        closeModal();
      } catch (e) {
        setError('root', { message: getApiErrorMessage(e) });
      }
    };

    return (
      <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4">
        <div
          ref={ref}
          className="w-full max-w-lg max-h-[90vh] overflow-y-auto bg-white rounded-2xl p-6 flex flex-col gap-4 shadow-xl"
        >
          <h3 className="text-center text-xl font-semibold">
            {isEdit ? 'Редактировать событие' : 'Новое мед. событие'}
          </h3>
          <form className="flex flex-col gap-3" onSubmit={handleSubmit(submit)}>
            <Controller
              name="type_action"
              control={control}
              render={({ field }) => (
                <Select
                  label="Тип"
                  options={TYPE_ACTION_OPTIONS.map((o) => ({
                    value: o.value,
                    label: o.label
                  }))}
                  value={field.value}
                  onChange={field.onChange}
                  onBlur={field.onBlur}
                  error={errors.status?.message}
                />
              )}
            />

            <Input
              label="Дата и время"
              type="datetime-local"
              {...register('date')}
              error={errors.date?.message}
            />

            <Controller
              name="status"
              control={control}
              render={({ field }) => (
                <Select
                  label="Статус"
                  options={MEDICAL_STATUS_OPTIONS.map((o) => ({
                    value: o.value,
                    label: o.label
                  }))}
                  value={field.value}
                  onChange={field.onChange}
                  onBlur={field.onBlur}
                  error={errors.status?.message}
                />
              )}
            />
            <Input label="Описание" {...register('description')} error={errors.description?.message} />
            <Input label="Заметки" {...register('notes')} error={errors.notes?.message} />
            <Input
              label="Интервал повтора (дней, 0 = нет)"
              type="number"
              min="0"
              {...register('interval_period', { valueAsNumber: true })}
              error={errors.interval_period?.message}
            />
            {errors.root && <p className="text-red-500 text-sm">{errors.root.message}</p>}
            <div className="flex gap-2">
              <Button type="button" intent="whiteBorder" onClick={closeModal}>
                Отмена
              </Button>
              <Button type="submit" disabled={isSubmitting}>
                Сохранить
              </Button>
            </div>
          </form>
        </div>
      </div>
    );
  },
);

MedicalEventModal.displayName = 'MedicalEventModal';
