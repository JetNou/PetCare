import { Header } from "@widgets/header";
import {Button} from "@shared/ui/Button.tsx";
import {LogHistoryCard} from "@shared/ui/Card.tsx";
import { PetCard, type PetResponse } from "@entities/pet";
import {useNavigate, useSearchParams} from "react-router";
import { useCallback, useEffect, useState} from "react";
import { usersApi, type UserProfile } from "@entities/user";
import { adminApi } from "@entities/admin";
import { getApiErrorMessage } from "@shared/lib/apiError";
import { resolveMediaUrl } from "@shared/lib/imageUrl";
import { EditProfileModal } from "@features/edit-profile/ui/EditProfileModal";
import { EditPetModal } from "@features/pet-edit/ui/EditPetModal";
import {useModal} from "@shared/hooks/useModal.ts";
import {useConfirmStore} from "@features/confirm/modal/confirm.store.ts";


export const AdminUserPage = () => {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams();
  const userId = Number(searchParams.get("userId"));

  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [pets, setPets] = useState<PetResponse[]>([]);
  const [logs, setLogs] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [editingPet, setEditingPet] = useState<PetResponse | null>(null);

  const {
    isOpen: isUserEditOpen,
    openModal: openUserEditModal,
    closeModal: closeUserEditModal,
    modalRef: userEditModalRef,
  } = useModal(false);

  const {
    isOpen: isPetEditOpen,
    openModal: openPetEditModal,
    closeModal: closePetEditModal,
    modalRef: petEditModalRef,
  } = useModal(false);

  const loadData = useCallback(async () => {
    if (!Number.isFinite(userId)) return;

    setError(null);

    const [userResult, petsResult, logsResult] = await Promise.allSettled([
      usersApi.getUserById(userId),
      adminApi.getAllPets(),
      adminApi.getUserLogs(userId, 50),
    ]);

    const errors: string[] = [];

    if (userResult.status === 'fulfilled') {
      setProfile(userResult.value.data);
    } else {
      errors.push(`Профиль: ${getApiErrorMessage(userResult.reason)}`);
      setProfile(null);
    }

    if (petsResult.status === 'fulfilled') {
      const petsData = petsResult.value.data;
      if (Array.isArray(petsData)) {
        setPets(petsData.filter((p) => p.user_id === userId));
      } else {
        console.error('Pets data is not an array:', petsData);
        setPets([]);
      }
    } else {
      errors.push(`Питомцы: ${getApiErrorMessage(petsResult.reason)}`);
      setPets([]);
    }

    if (logsResult.status === 'fulfilled') {
      const logsData = logsResult.value.data;
      if (Array.isArray(logsData)) {
        setLogs(logsData);
      } else {
        console.error('Logs data is not an array:', logsData);
        setLogs([]);
      }
    } else {
      errors.push(`Логи: ${getApiErrorMessage(logsResult.reason)}`);
      setLogs([]);
    }

    if (errors.length > 0) {
      setError(errors.join('\n'));
    }
  }, [userId]);

  useEffect(() => {
    void loadData();
  }, [loadData]);

  const handleDeleteUser = () => {
    if (!profile) return;

    useConfirmStore.getState().open({
      message: `Удалить пользователя @${profile.user_login}?`,
      okText: "Да",
      cancelText: "Нет",
      onCancel: () => {},
      onConfirm: async () => {
        try {
          await adminApi.deleteUser(profile.user_id);
          navigate('/admin');
        } catch (e) {
          setError(getApiErrorMessage(e));
        }
      }
    })
  };

  const handleResetUserAvatar = () => {
    if (!profile) return;

    useConfirmStore.getState().open({
      message: `Сбросить аватар пользователя @${profile.user_login} до стандартного?`,
      okText: "Да",
      cancelText: "Нет",
      onCancel: () => {},
      onConfirm: async () => {
        try {
          await adminApi.resetUserAvatar(profile.user_id);
          await loadData();
        } catch (e) {
          setError(getApiErrorMessage(e));
        }
      }
    })
  };

  const handleOpenPetEdit = (pet: PetResponse) => {
    setEditingPet(pet);
    openPetEditModal();
  };

  const handleDeletePet = (pet: PetResponse) => {
    useConfirmStore.getState().open({
      message: `Удалить питомца «${pet.name}»?`,
      okText: "Да",
      cancelText: "Нет",
      onCancel: () => {},
      onConfirm: async () => {
        try {
          await adminApi.deletePet(pet.pet_id);
          await loadData();
        } catch (e) {
          setError(getApiErrorMessage(e));
        }
      }
    })
  };

  const handleResetPetAvatar = (pet: PetResponse) => {
    useConfirmStore.getState().open({
      message: `Сбросить аватар питомца «${pet.name}» до стандартного?`,
      okText: "Да",
      cancelText: "Нет",
      onCancel: () => {},
      onConfirm: async () => {
        try {
          await adminApi.resetPetAvatar(pet.pet_id);
          await loadData();
        } catch (e) {
          setError(getApiErrorMessage(e));
        }
      }
    })
  };

  const avatarUrl = profile?.user_avatar ? resolveMediaUrl(profile.user_avatar) : undefined;

  if (!Number.isFinite(userId)) {
    return (
      <>
        <Header type="logoAndProfile" />
        <main className="container mt-8">
          <p>Укажите пользователя: /admin-user?userId=…</p>
        </main>
      </>
    );
  }

  return (
    <>
      <Header type="logoAndProfile" />

      <main className="container flex flex-col my-6 md:my-10">
        <button
          type="button"
          className="flex gap-1 items-center cursor-pointer"
          onClick={() => navigate(-1)}
        >
          <svg className="w-5 h-4 rotate-180" viewBox="0 0 27 23" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M26.0607 12.1066C26.6464 11.5208 26.6464 10.571 26.0607 9.98524L16.5147 0.439297C15.9289 -0.14649 14.9792 -0.14649 14.3934 0.439297C13.8076 1.02508 13.8076 1.97483 14.3934 2.56062L22.8787 11.0459L14.3934 19.5312C13.8076 20.117 13.8076 21.0667 14.3934 21.6525C14.9792 22.2383 15.9289 22.2383 16.5147 21.6525L26.0607 12.1066ZM0 11.0459L0 12.5459H25V11.0459V9.5459H0L0 11.0459Z" fill="#F97316"/>
          </svg>
          <h3 className="text-brand-primary">Назад</h3>
        </button>
        {error && <p className="text-red-600 mt-4">{error}</p>}

        <div className="mt-6 flex flex-col gap-6 md:mt-10 2xl:h-[75vh] 2xl:max-h-200 2xl:flex-row 2xl:items-stretch">
          
          <div className="flex w-full flex-col gap-y-6 2xl:w-2/3 2xl:min-h-0">
            
            <section className="flex flex-col lg:flex-row p-5 gap-6 md:p-8 bg-white rounded-2xl shrink-0">
              <div className="flex flex-col sm:flex-row items-center sm:items-start gap-5 w-full">
                <div className="flex w-28 h-28 md:w-36 md:h-36 border border-black items-center justify-center rounded-full shrink-0 overflow-hidden bg-brand-cream">
                  <img 
                    src={avatarUrl} 
                    alt="" 
                    className={`${avatarUrl?.includes("user-standart") ? 'w-2/3 h-2/3' : 'w-full h-full'} object-cover rounded-full`} 
                  />
                </div>
                <div className="flex flex-col text-center sm:text-left">
                  <div className="flex justify-center sm:justify-start items-center gap-2">
                    <h2>{profile?.user_full_name ?? "…"}</h2>
                  </div>
                  <div className="mt-2 space-y-1">
                    <h3 className="font-normal">@{profile?.user_login ?? "…"}</h3>
                    <h3 className="font-normal">{profile?.user_email ?? "…"}</h3>
                    <h3 className="font-normal">Статус: {profile?.status ?? "…"}</h3>
                  </div>
                  <div className="mt-4 flex flex-wrap gap-2">
                    <Button type="button" size="small" onClick={openUserEditModal}>
                      Редактировать профиль
                    </Button>
                    <Button type="button" size="small" intent="whiteBorder" onClick={() => void handleResetUserAvatar()}>
                      Сбросить аватар
                    </Button>
                    <Button type="button" size="small" intent="red" onClick={() => void handleDeleteUser()}>
                      Удалить пользователя
                    </Button>
                  </div>
                </div>
              </div>
            </section>

            <section className="flex flex-col bg-white rounded-2xl flex-1 min-h-80 max-h-125 overflow-hidden 2xl:max-h-none 2xl:min-h-0">
              <h2 className="m-4 md:m-8 shrink-0">Питомцы:</h2>
              
              <div className="flex-1 overflow-y-auto px-4 pb-6 min-h-0">
                <div className="grid gap-5 grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 2xl:grid-cols-2 justify-center place-items-start">
                  {pets.map((p) => (
                    <div key={p.pet_id} className="w-full flex flex-col gap-3">
                      <PetCard
                        pet={p}
                        className="cursor-default"
                      />
                      <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
                        <Button className="text-xs sm:text-xs md:text-xs" type="button" size="small" onClick={() => handleOpenPetEdit(p)}>
                          Редактировать
                        </Button>
                        <Button className="text-xs sm:text-xs md:text-xs" type="button" size="small" intent="whiteBorder" onClick={() => void handleResetPetAvatar(p)}>
                          Сбросить аватар
                        </Button>
                        <Button className="text-xs sm:text-xs md:text-xs" type="button" size="small" intent="red" onClick={() => void handleDeletePet(p)}>
                          Удалить
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
                {pets.length === 0 && <p className="text-center text-brand-wood">Нет питомцев</p>}
              </div>
            </section>

          </div>

          <div className="flex w-full flex-col rounded-2xl bg-white p-6 2xl:w-1/3 2xl:min-h-0">
            <h2 className="text-center shrink-0 mb-4">Логи</h2>
            
            <div className="flex-1 flex flex-col gap-5 overflow-y-auto min-h-0 pr-2">
              {logs.length === 0 && <p className="text-sm text-gray-500">Нет записей</p>}
              {logs.map((line, i) => (
                <LogHistoryCard key={i}>{line}</LogHistoryCard>
              ))}
            </div>
          </div>
          
        </div>
      </main>

      {isUserEditOpen && profile && (
        <EditProfileModal
          ref={userEditModalRef}
          profile={profile}
          title="Редактировать пользователя"
          closeModal={closeUserEditModal}
          onSaved={loadData}
          saveProfile={async (data) => {
            await adminApi.updateUser(profile.user_id, {
              user_login: data.user_login,
              user_full_name: data.user_full_name,
              user_email: data.user_email,
            });
          }}
        />
      )}

      {isPetEditOpen && editingPet && (
        <EditPetModal
          ref={petEditModalRef}
          pet={editingPet}
          closeModal={() => {
            closePetEditModal();
            setEditingPet(null);
          }}
          onSaved={loadData}
          savePet={async (data) => {
            if (typeof data.weight !== 'number') return;
            await adminApi.updatePet(editingPet.pet_id, {
              name: data.name,
              breed: data.breed || null,
              color: data.color || null,
              gender: data.gender || null,
              date_birth: data.date_birth || null,
              chip: data.chip || null,
              weight: data.weight,
            });
          }}
        />
      )}
    </>
  )
}
