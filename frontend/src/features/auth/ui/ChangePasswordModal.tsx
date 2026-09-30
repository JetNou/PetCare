import { forwardRef, useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import {Input, InputPassword} from '@shared/ui/Input.tsx';
import { Button } from '@shared/ui/Button.tsx';
import { authApi } from '@features/auth/api/auth.api';
import {
  changePasswordSchema,
  type ChangePasswordFormData,
} from '@features/auth/model/change-password.schema.ts';
import { getApiErrorMessage } from '@shared/lib/apiError';

type PasswordChangeStep = 'request' | 'confirm';

interface ChangePasswordModalProps {
  closeModal: () => void;
}

export const ChangePasswordModal = forwardRef<HTMLDivElement, ChangePasswordModalProps>(
  ({ closeModal }, ref) => {
    const [step, setStep] = useState<PasswordChangeStep>('request');
    const [requestError, setRequestError] = useState<string | null>(null);

    const {
      register,
      handleSubmit,
      formState: { errors, isSubmitting },
      setError,
      reset,
    } = useForm<ChangePasswordFormData>({
      resolver: zodResolver(changePasswordSchema),
    });

    const handleRequestPasswordReset = async () => {
      try {
        setRequestError(null);
        await authApi.requestPasswordReset();
        setStep('confirm');
      } catch (e) {
        setRequestError(getApiErrorMessage(e));
      }
    };

    const onSubmitConfirm = async (data: ChangePasswordFormData) => {
      try {
        await authApi.confirmPasswordReset(data);
        reset();
        setStep('request');
        closeModal();
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
          {step === 'request' && (
            <>
              <h3 className="text-center text-xl font-semibold">Смена пароля</h3>
              <p className="text-center text-sm text-gray-600">
                Мы отправим на вашу почту письмо со ссылкой подтверждения. Перейдите по ссылке, получите код и введите его здесь.
              </p>
              {requestError && (
                <p className="text-red-500 text-sm text-center">{requestError}</p>
              )}
              <div className="flex gap-2">
                <Button intent="whiteBorder" type="button" onClick={closeModal}>
                  Отмена
                </Button>
                <Button
                  type="button"
                  onClick={() => void handleRequestPasswordReset()}
                  disabled={isSubmitting}
                >
                  Отправить письмо
                </Button>
              </div>
            </>
          )}

          {step === 'confirm' && (
            <>
              <h3 className="text-center text-xl font-semibold">Подтверждение смены пароля</h3>
              <p className="text-center text-sm text-gray-600">
                Введите код из письма и новый пароль
              </p>

              <form className="flex flex-col gap-4" onSubmit={handleSubmit(onSubmitConfirm)}>
                <Input
                  label="Код подтверждения"
                  placeholder="Введите код из письма"
                  {...register('token')}
                  error={errors.token?.message}
                />

                <InputPassword
                  label="Новый пароль"
                  placeholder="Минимум 8 символов, буквы и цифры"
                  {...register('new_password')}
                  error={errors.new_password?.message}
                />

                {errors.root && (
                  <p className="text-red-500 text-sm text-center">{errors.root.message}</p>
                )}

                <div className="flex gap-2">
                  <Button
                    intent="whiteBorder"
                    type="button"
                    onClick={() => setStep('request')}
                  >
                    Назад
                  </Button>
                  <Button type="submit" disabled={isSubmitting}>
                    Сохранить пароль
                  </Button>
                </div>
              </form>
            </>
          )}
        </div>
      </div>
    );
  }
);

ChangePasswordModal.displayName = 'ChangePasswordModal';
