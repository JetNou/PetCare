import { Header } from "@widgets/header";
import {Button} from "@shared/ui/Button.tsx";
import {useNavigate} from "react-router";
import { useSessionStore, usersApi, UserStatus } from "@entities/user";
import { getApiErrorMessage } from "@shared/lib/apiError";
import { resolveMediaUrl } from "@shared/lib/imageUrl";
import { useCallback, useEffect, useRef, useState } from "react";
import { ChangePasswordModal } from "@features/auth/ui/ChangePasswordModal";
import { logoutClient } from "@features/auth/lib/logoutClient";
import {useModal} from "@shared/hooks/useModal.ts";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Input } from "@shared/ui/Input.tsx";
import {
  editProfileSchema,
  type EditProfileFormData,
} from "@features/edit-profile/model/edit-profile.schema.ts";
import {useConfirmStore} from "@features/confirm/modal/confirm.store.ts";


export const ProfilePage = () => {
  const navigate = useNavigate();
  const { user, setUser } = useSessionStore();
  const [loadError, setLoadError] = useState<string | null>(null);
  const [isEditingProfile, setIsEditingProfile] = useState(false);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const photoInputRef = useRef<HTMLInputElement>(null);
  const { isOpen: isPasswordModalOpen, openModal: openPasswordModal, closeModal: closePasswordModal, modalRef: passwordModalRef } = useModal(false);
  const { isOpen: isEditModalOpen, openModal: openEditModal, closeModal: closeEditModal, modalRef: editModalRef } = useModal(false);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
    setError,
    reset: resetForm,
  } = useForm<EditProfileFormData>({
    resolver: zodResolver(editProfileSchema),
    defaultValues: {
      user_login: user?.user_login,
      user_full_name: user?.user_full_name,
      user_email: user?.user_email,
    },
  });

  const load = useCallback(async () => {
    try {
      setLoadError(null);
      const { data } = await usersApi.getProfile();
      setUser(data);
      resetForm({
        user_login: data.user_login,
        user_full_name: data.user_full_name,
        user_email: data.user_email,
      });
    } catch (e) {
      setLoadError(getApiErrorMessage(e));
    }
  }, [setUser, resetForm]);

  useEffect(() => {
    void load();
  }, [load]);

  useEffect(() => {
    if (!isEditModalOpen) return;
    const onDoc = (e: MouseEvent) => {
      if (editModalRef.current && !editModalRef.current.contains(e.target as Node)) {
        closeEditModal();
      }
    };
    document.addEventListener("mousedown", onDoc);
    return () => document.removeEventListener("mousedown", onDoc);
  }, [isEditModalOpen, closeEditModal]);

  const profile = user;
  const avatarUrl = profile?.user_avatar ? resolveMediaUrl(profile.user_avatar) : undefined;

  const handleDeleteAccount = () => {
    useConfirmStore.getState().open({
      message: "Удалить аккаунт? Письмо со ссылкой восстановления придёт на почту.",
      okText: "Да",
      cancelText: "Нет",
      onCancel: () => {},
      onConfirm: async () => {
        try {
          await usersApi.deleteProfile();
          await logoutClient();
          navigate("/");
        } catch (e) {
          setLoadError(getApiErrorMessage(e));
        }
      }
    })

  };

  const handleLogout = async () => {
    await logoutClient();
    navigate("/");
  };

  const handleDeleteIcon = () => {
    useConfirmStore.getState().open({
      message: "Удалить аватарку?",
      okText: "Да",
      cancelText: "Нет",
      onCancel: () => {},
      onConfirm: () => {
        usersApi.deleteAvatar()
          .then(() => void load())
          .catch(e => setLoadError(getApiErrorMessage(e)));
      }
    })
  }

  const handleUploadPhoto = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file || !user?.user_id) return;
    try {
      await usersApi.updateProfile({ photo: file });
      await load();
    } catch (err) {
      setLoadError(getApiErrorMessage(err));
    } finally {
      e.target.value = "";
    }
  };

  const onSubmitProfile = async (data: EditProfileFormData) => {
    if (!profile) return;
    try {
      setLoadError(null);
      setSuccessMessage(null);
      const emailChanged = data.user_email !== profile.user_email;

      await usersApi.updateProfile({
        user_login: data.user_login,
        user_full_name: data.user_full_name,
        user_email: data.user_email,
        photo: null,
      });

      if (!emailChanged) {
        await load();
      }

      setIsEditingProfile(false);
      closeEditModal();

      if (emailChanged) {
        setSuccessMessage('Почта изменена! Письмо подтверждения отправлено на новый адрес. Перенаправляем на верификацию...');
        setTimeout(async () => {
          await logoutClient();
          navigate('/verify-email');
        }, 2000);
      } else {
        setSuccessMessage('Профиль успешно обновлён');
        setTimeout(() => setSuccessMessage(null), 3000);
      }

    } catch (e) {
      setError('root', { message: getApiErrorMessage(e) });
    }
  };

  return (
    <>
      <Header type="onlyAdminButton" />

      <main className="flex items-center justify-center p-6">

        <div className="relative bg-white rounded-2xl mt-12">

        <button
          type="button"
          className="flex gap-1 items-center cursor-pointer self-start absolute -top-13 left-0"
          onClick={() => navigate(-1)}
        >
          <svg className="w-5 h-4 rotate-180" viewBox="0 0 27 23" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M26.0607 12.1066C26.6464 11.5208 26.6464 10.571 26.0607 9.98524L16.5147 0.439297C15.9289 -0.14649 14.9792 -0.14649 14.3934 0.439297C13.8076 1.02508 13.8076 1.97483 14.3934 2.56062L22.8787 11.0459L14.3934 19.5312C13.8076 20.117 13.8076 21.0667 14.3934 21.6525C14.9792 22.2383 15.9289 22.2383 16.5147 21.6525L26.0607 12.1066ZM0 11.0459L0 12.5459H25V11.0459V9.5459H0L0 11.0459Z" fill="#F97316"/>
          </svg>
          <h3 className="text-brand-primary">Назад</h3>
        </button>

          <div className="flex flex-col items-center bg-brand-gradient p-6 gap-y-2 rounded-2xl">

            <div className="relative flex w-28 h-28 md:w-36 md:h-36 border border-black items-center justify-center rounded-full shrink-0 bg-brand-cream">
              <input
                ref={photoInputRef}
                type="file"
                accept="image/*"
                className="hidden"
                onChange={handleUploadPhoto}
              />

              <button
                type="button"
                className="w-full h-full rounded-full overflow-hidden cursor-pointer group"
                onClick={() => photoInputRef.current?.click()}
                title="Сменить фото"
              >
                <img
                  src={avatarUrl}
                  alt=""
                  className={`${avatarUrl?.includes("user-standart") ? 'w-2/3 h-2/3 m-auto' : 'w-full h-full'} object-cover`}
                />

                <div className="absolute inset-0 bg-black/40 rounded-full flex flex-col items-center justify-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity duration-200">
                  <svg className="w-7 h-7 text-white" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M9 3L7.17 5H4C2.9 5 2 5.9 2 7V19C2 20.1 2.9 21 4 21H20C21.1 21 22 20.1 22 19V7C22 5.9 21.1 5 20 5H16.83L15 3H9ZM12 18C9.24 18 7 15.76 7 13C7 10.24 9.24 8 12 8C14.76 8 17 10.24 17 13C17 15.76 14.76 18 12 18Z" fill="white"/>
                    <circle cx="12" cy="13" r="3" fill="white"/>
                  </svg>
                  <span className="text-white text-xs font-medium">Сменить фото</span>
                </div>
              </button>

              <button
                className="absolute top-7/10 left-7/10 flex w-10 h-10 items-center justify-center bg-red-600 rounded-full cursor-pointer hover:scale-103 transition-transform duration-200"
                onClick={(e) => {
                  e.stopPropagation();
                  handleDeleteIcon();
                }}
              >
                <svg className="w-2/3 h-2/3" viewBox="0 0 40 40" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M35 11.2168C34.9667 11.2168 34.9167 11.2168 34.8667 11.2168C26.05 10.3335 17.25 10.0001 8.53333 10.8835L5.13333 11.2168C4.43333 11.2835 3.81667 10.7835 3.75 10.0835C3.68333 9.38346 4.18333 8.78346 4.86667 8.71679L8.26667 8.38346C17.1333 7.48346 26.1167 7.83346 35.1167 8.71679C35.8 8.78346 36.3 9.40012 36.2333 10.0835C36.1833 10.7335 35.6333 11.2168 35 11.2168Z" fill="white"/>
                  <path d="M14.1667 9.5335C14.1 9.5335 14.0333 9.5335 13.95 9.51683C13.2833 9.40016 12.8167 8.75016 12.9333 8.0835L13.3 5.90016C13.5667 4.30016 13.9333 2.0835 17.8167 2.0835H22.1833C26.0833 2.0835 26.45 4.3835 26.7 5.91683L27.0667 8.0835C27.1833 8.76683 26.7167 9.41683 26.05 9.51683C25.3667 9.6335 24.7167 9.16683 24.6167 8.50016L24.25 6.3335C24.0167 4.8835 23.9667 4.60016 22.2 4.60016H17.8333C16.0667 4.60016 16.0333 4.8335 15.7833 6.31683L15.4 8.4835C15.3 9.10016 14.7667 9.5335 14.1667 9.5335Z" fill="white"/>
                  <path d="M25.35 37.9168H14.65C8.83333 37.9168 8.6 34.7001 8.41667 32.1001L7.33333 15.3168C7.28333 14.6335 7.81667 14.0335 8.5 13.9835C9.2 13.9501 9.78333 14.4668 9.83333 15.1501L10.9167 31.9335C11.1 34.4668 11.1667 35.4168 14.65 35.4168H25.35C28.85 35.4168 28.9167 34.4668 29.0833 31.9335L30.1667 15.1501C30.2167 14.4668 30.8167 13.9501 31.5 13.9835C32.1833 14.0335 32.7167 14.6168 32.6667 15.3168L31.5833 32.1001C31.4 34.7001 31.1667 37.9168 25.35 37.9168Z" fill="white"/>
                  <path d="M22.7667 28.75H17.2167C16.5333 28.75 15.9667 28.1833 15.9667 27.5C15.9667 26.8167 16.5333 26.25 17.2167 26.25H22.7667C23.45 26.25 24.0167 26.8167 24.0167 27.5C24.0167 28.1833 23.45 28.75 22.7667 28.75Z" fill="white"/>
                  <path d="M24.1667 22.0835H15.8333C15.15 22.0835 14.5833 21.5168 14.5833 20.8335C14.5833 20.1502 15.15 19.5835 15.8333 19.5835H24.1667C24.85 19.5835 25.4167 20.1502 25.4167 20.8335C25.4167 21.5168 24.85 22.0835 24.1667 22.0835Z" fill="white"/>
                </svg>
              </button>
            </div>

            {!isEditingProfile ? (
              <>
                <h2>{profile?.user_full_name ?? "…"}</h2>
                <h3>@{profile?.user_login ?? "…"}</h3>
                <h3>{profile?.user_email ?? "…"}</h3>
                {profile?.status === UserStatus.Registered ? (
                  <p className="text-sm text-center px-2">Подтвердите email — после смены почты статус снова может стать «ожидает подтверждения».</p>
                ) : (loadError && <p className="text-red-500 text-sm text-center">{loadError}</p>)}
                {successMessage && (
                  <p className="text-green-600 text-sm text-center">{successMessage}</p>
                )}

                <div className="flex gap-2 justify-center mt-2">
                  <Button
                    type="button"
                    onClick={() => {
                      setIsEditingProfile(true);
                      openEditModal();
                    }}
                  >
                    Редактировать
                  </Button>
                  <Button
                    type="button"
                    onClick={openPasswordModal}
                  >
                    Сменить пароль
                  </Button>
                </div>
              </>
            ) : (
              <form
                className="w-full flex flex-col gap-3"
                onSubmit={handleSubmit(onSubmitProfile)}
              >
                <Input 
                  label="Логин"
                  className="bg-white"
                  {...register('user_login')} 
                  error={errors.user_login?.message}
                />
                <Input 
                  label="Имя"
                  className="bg-white"
                  {...register('user_full_name')} 
                  error={errors.user_full_name?.message}
                />
                <Input 
                  label="Email" 
                  type="email"
                  className="bg-white"
                  {...register('user_email')} 
                  error={errors.user_email?.message}
                />
                {errors.root && (
                  <p className="text-red-500 text-sm">{errors.root.message}</p>
                )}
                {successMessage && (
                  <p className="text-green-600 text-sm text-center">{successMessage}</p>
                )}
                <div className="flex gap-2 justify-center">
                  <Button 
                    type="button" 
                    intent="whiteBorder"
                    disabled={isSubmitting || !!successMessage}
                    onClick={() => {
                      setIsEditingProfile(false);
                      setSuccessMessage(null);
                      closeEditModal();
                    }}
                  >
                    Отмена
                  </Button>
                  <Button 
                    type="submit"
                    disabled={isSubmitting || !!successMessage}
                  >
                    Сохранить
                  </Button>
                </div>
              </form>
            )}
          </div>
          <div className="grid grid-cols-2 gap-4 lg:grid-cols-[1fr_2fr_1fr] p-4">
            <Button
              intent="red"
              className="lg:col-start-1 lg:row-start-1"
              type="button"
              onClick={() => void handleDeleteAccount()}
            >
              Удалить аккаунт
            </Button>
            <Button
              intent="whiteBorder"
              className="lg:col-start-3 lg:row-start-1"
              type="button"
              onClick={() => void handleLogout()}
            >
              Выйти из аккаунта
            </Button>
          </div>

        </div>

      </main>

      {isPasswordModalOpen && (
        <ChangePasswordModal ref={passwordModalRef} closeModal={closePasswordModal} />
      )}
    </>
  )
}