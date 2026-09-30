import { Input } from '@shared/ui/Input.tsx';
import { Button } from '@shared/ui/Button.tsx';
import { forwardRef } from 'react';
import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { petCreateSchema, type PetCreateFormValues } from '@features/pet-create/model/pet.schema.ts';
import { petsApi } from '@entities/pet';
import { getApiErrorMessage } from '@shared/lib/apiError';
import { Select } from '@shared/ui/Select';

interface CreatePetModalProps {
  closeModal: () => void;
  onCreated: () => void;
}

export const CreatePetModal = forwardRef<HTMLDivElement, CreatePetModalProps>(
  ({ closeModal, onCreated }, ref) => {
    const {
      register,
      control,
      handleSubmit,
      formState: { errors, isSubmitting },
      setError,
    } = useForm<PetCreateFormValues>({
      resolver: zodResolver(petCreateSchema),
      defaultValues: {
        name: '',
        gender: '',
        date_birth: '',
        weight: 1,
        breed: '',
        color: '',
        chip: '',
      },
    });

    const onSubmit = async (data: PetCreateFormValues) => {
      try {
        if (typeof data.weight !== 'number') {
          setError('weight', { message: 'Укажите вес питомца' });
          return;
        }
        await petsApi.createPet({
          name: data.name,
          weight: data.weight,
          gender: data.gender?.trim() ? data.gender : null,
          date_birth: data.date_birth?.trim() ? data.date_birth : null,
          breed: data.breed?.trim() ? data.breed : null,
          color: data.color?.trim() ? data.color : null,
          chip: data.chip?.trim() ? data.chip : null,
        });
        onCreated();
        closeModal();
      } catch (e) {
        setError('root', { message: getApiErrorMessage(e) });
      }
    };

    return (
      <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4">
        <div
          className="w-full max-w-md bg-white rounded-2xl p-6 sm:p-10 flex flex-col gap-y-4 shadow-xl"
          ref={ref}
        >
          <h3 className="text-center text-xl font-semibold">Добавить питомца</h3>
          <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-y-3">
            <Input label="Кличка" {...register('name')} error={errors.name?.message} />
            <Input label="Порода" {...register('breed')} error={errors.breed?.message} />
            <Input label="Окрас" {...register('color')} error={errors.color?.message} />

            <Controller
              name="gender"
              control={control}
              render={({ field }) => (
                <Select
                  label="Пол"
                  options={[
                    { value: 'male', label: 'Самец' },
                    { value: 'female', label: 'Самка' },
                    { value: 'none', label: 'Не указывать' },
                  ]}
                  value={field.value}
                  onChange={field.onChange}
                  onBlur={field.onBlur}
                  error={errors.gender?.message}
                />
              )}
            />

            <Input label="Дата рождения" type="date" {...register('date_birth')} error={errors.date_birth?.message} />
            <Input label="Чип" {...register('chip')} error={errors.chip?.message} />
            <Input
              label="Вес, кг"
              type="text"
              step="0.01"
              {...register('weight', { valueAsNumber: true })}
              error={errors.weight?.message}
            />
            {errors.root && <p className="text-red-500 text-sm">{errors.root.message}</p>}
            <div className="flex gap-2">
              <Button intent="whiteBorder" type="button" onClick={closeModal}>
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

CreatePetModal.displayName = 'CreatePetModal';