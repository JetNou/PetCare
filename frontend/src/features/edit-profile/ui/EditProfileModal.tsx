import { forwardRef, useRef } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { Input } from '@shared/ui/Input.tsx';
import { Button } from '@shared/ui/Button.tsx';
import { usersApi, useSessionStore, type UserProfile } from '@entities/user';
import {
  editProfileSchema,
  type EditProfileFormData,
} from '@features/edit-profile/model/edit-profile.schema.ts';
import { getApiErrorMessage } from '@shared/lib/apiError';
import {useNavigate} from "react-router";
import {logoutClient} from "@features/auth/lib/logoutClient.ts";

interface EditProfileModalProps {
  profile: UserProfile;
  closeModal: () => void;
  title?: string;
  onSaved?: () => void | Promise<void>;
  saveProfile?: (data: EditProfileFormData, photo?: File | null) => Promise<void>;
}

export const EditProfileModal = forwardRef<HTMLDivElement, EditProfileModalProps>(
  ({ profile, closeModal, title, onSaved, saveProfile }, ref) => {
    const setUser = useSessionStore((s) => s.setUser);
    const {
      register,
      handleSubmit,
      formState: { errors, isSubmitting },
      setError,
    } = useForm<EditProfileFormData>({
      resolver: zodResolver(editProfileSchema),
      defaultValues: {
        user_login: profile.user_login,
        user_full_name: profile.user_full_name,
        user_email: profile.user_email,
      },
    });
    const fileInputRef = useRef<HTMLInputElement>(null);
    const navigate = useNavigate();

    const onSubmit = async (data: EditProfileFormData, photo?: File | null) => {
      try {
        if (saveProfile) {
          await saveProfile(data, photo);
          closeModal();
          await onSaved?.();
          return;
        }

        const emailChanged = data.user_email !== profile.user_email;

        const { data: updated } = await usersApi.updateProfile({
          user_login: data.user_login,
          user_full_name: data.user_full_name,
          user_email: data.user_email,
          photo: photo ?? null,
        });

        setUser(updated);
        closeModal();
        await onSaved?.();

        if (emailChanged) {
          await logoutClient();
          navigate('/login');
        }
      } catch (e) {
        setError('root', { message: getApiErrorMessage(e) });
      }
    };

    return (
      <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4">
        <div
          ref={ref}
          className="w-full max-w-md bg-white rounded-2xl p-6 sm:p-8 flex flex-col gap-4 shadow-xl"
        >
          <h3 className="text-center text-xl font-semibold">{title ?? 'Редактировать профиль'}</h3>
          <form
            className="flex flex-col gap-4"
            onSubmit={handleSubmit((data) => {
              const file = fileInputRef.current?.files?.[0];
              return onSubmit(data, file);
            })}
          >
            <Input label="Логин" {...register('user_login')} error={errors.user_login?.message} />
            <Input label="Имя" {...register('user_full_name')} error={errors.user_full_name?.message} />
            <Input label="Email" type="email" {...register('user_email')} error={errors.user_email?.message} />

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

EditProfileModal.displayName = 'EditProfileModal';