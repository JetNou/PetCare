import { forwardRef, useEffect, useRef } from 'react';
import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { Input } from '@shared/ui/Input.tsx';
import { Button } from '@shared/ui/Button.tsx';
import { petsApi, type PetResponse } from '@entities/pet';
import { getApiErrorMessage } from '@shared/lib/apiError';
import { Select } from '@/shared/ui/Select';
import {
  type PetCreateFormValues, petCreateSchema
} from "@features/pet-create/model/pet.schema.ts";


interface EditPetModalProps {
  pet: PetResponse;
  closeModal: () => void;
  onSaved: () => void | Promise<void>;
  savePet?: (data: PetCreateFormValues, photo?: File | null) => Promise<void>;
}

export const EditPetModal = forwardRef<HTMLDivElement, EditPetModalProps>(
  ({ pet, closeModal, onSaved, savePet }, ref) => {
    const {
      register,
      handleSubmit,
      control,
      reset,
      formState: { errors, isSubmitting },
      setError,
    } = useForm<PetCreateFormValues>({
      resolver: zodResolver(petCreateSchema),
      defaultValues: {
        name: pet.name,
        breed: pet.breed ?? '',
        color: pet.color ?? '',
        gender: pet.gender ?? '',
        date_birth: pet.date_birth ?? '',
        chip: pet.chip ?? '',
        weight: pet.weight ?? 0,
      },
    });
    const fileInputRef = useRef<HTMLInputElement>(null);

    useEffect(() => {
      reset({
        name: pet.name,
        breed: pet.breed ?? '',
        color: pet.color ?? '',
        gender: pet.gender ?? '',
        date_birth: pet.date_birth ?? '',
        chip: pet.chip ?? '',
        weight: pet.weight ?? 0,
      });
    }, [pet, reset]);

    const submit = async (data: PetCreateFormValues) => {
      try {
        if (typeof data.weight !== 'number') {
          setError('weight', { message: 'Укажите вес питомца' });
          return;
        }
        const file = fileInputRef.current?.files?.[0];

        if (savePet) {
          await savePet(data, file);
        } else {
          await petsApi.updatePet(pet.pet_id, {
            name: data.name,
            breed: data.breed || null,
            color: data.color || null,
            gender: data.gender || null,
            date_birth: data.date_birth || null,
            chip: data.chip || null,
            weight: data.weight,
          });
        }

        await onSaved();
        closeModal();
      } catch (e) {
        setError('root', { message: getApiErrorMessage(e) });
      }
    };

    return (
      <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4">
        <div ref={ref} className="w-full max-w-md bg-white rounded-2xl p-6 flex flex-col gap-4 shadow-xl">
          <h3 className="text-center text-xl font-semibold">Редактировать питомца</h3>
          <form className="flex flex-col gap-3" onSubmit={handleSubmit(submit)}>
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
            <Input label="Вес, кг" type="number" step="0.01" {...register('weight', { valueAsNumber: true })} error={errors.weight?.message} />

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

EditPetModal.displayName = 'EditPetModal';
