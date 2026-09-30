import { Button } from "@/shared/ui/Button";
import { Input } from "@/shared/ui/Input";
import { forwardRef } from "react";
import { restorePetSchema, type RestorePetFormValues } from "@features/restore-pet/model/restore-pet.schema.ts";
import { useForm } from "react-hook-form";
import { zodResolver } from '@hookform/resolvers/zod';
import { petsApi } from "@entities/pet";

interface RestoreAPetProps {
  closeModal: () => void;
  onCreated: () => void;
}

export const RestoreAPet = forwardRef<HTMLDivElement, RestoreAPetProps>(({ closeModal, onCreated }, ref) => {
    const {
      register,
      handleSubmit,
      formState: { errors, isSubmitting },
      setError,
    } = useForm<RestorePetFormValues>({
      resolver: zodResolver(restorePetSchema),
    });

    const onSubmit = async (data: RestorePetFormValues) => {
        try {
          await petsApi.restorePet(data.token)
          onCreated()
        } catch (e) {
            setError('root', { message: 'Ошибка при восстановлении питомца' });
        }
    }


    return (
        <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4">
                <div
                  className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-full max-w-md bg-white rounded-2xl p-6 sm:p-10 flex flex-col gap-y-4 shadow-xl"
                  ref={ref}
                >
                  <h3 className="text-center text-xl font-semibold">Восстановить питомца</h3>
                  <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-y-3">
                    <Input label="Токен" {...register('token')} error={errors.token?.message} />
                    <div className="flex gap-2">
                      <Button intent="whiteBorder" type="button" onClick={closeModal}>
                        Отмена
                      </Button>
                      <Button type="submit" disabled={isSubmitting}>
                        Восстановить
                      </Button>
                    </div>
                </form>
            </div>
        </div>
    )
})