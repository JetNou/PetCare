import { Header } from "@widgets/header";
import { PetCard, petsApi, type PetResponse } from "@entities/pet";
import {CreatePetModal} from "@features/pet-create/ui/CreatePetModal.tsx";
import {useCallback, useEffect, useState} from "react";
import {useNavigate} from "react-router";
import { getApiErrorMessage } from "@shared/lib/apiError";
import {RestoreAPet} from "@features/restore-pet/ui/RestoreAPet.tsx";
import {Button} from "@shared/ui/Button.tsx";
import {useModal} from "@shared/hooks/useModal.ts";
import { cn } from "@shared/utils/utils.ts";

type PetCardView = "default" | "compact" | "spotlight";

const PET_CARD_VIEW_KEY = "petcare:pets-card-view";

const petCardViewOptions: Array<{
  value: PetCardView;
  label: string;
}> = [
  { value: "default", label: "Классика" },
  { value: "compact", label: "Компактно"},
  { value: "spotlight", label: "Акцент" },
];

export const PetsPage = () => {
  const navigate = useNavigate()
  const [pets, setPets] = useState<PetResponse[]>([])
  const [loadError, setLoadError] = useState<string | null>(null)
  const [cardView, setCardView] = useState<PetCardView>(() => {
    if (typeof window === "undefined") return "default";

    const savedView = window.localStorage.getItem(PET_CARD_VIEW_KEY);
    return savedView === "compact" || savedView === "spotlight" || savedView === "default"
      ? savedView
      : "default";
  })

  const loadPets = useCallback(async () => {
    try {
      setLoadError(null)
      const { data } = await petsApi.getMyPets()
      setPets(data)
    } catch (e) {
      setLoadError(getApiErrorMessage(e))
    }
  }, [])

  useEffect(() => {
    void loadPets()
  }, [loadPets])

  useEffect(() => {
    window.localStorage.setItem(PET_CARD_VIEW_KEY, cardView);
  }, [cardView]);

  const {
    isOpen: isRestoreAPetOpen,
    openModal: openRestoreAPetModal,
    closeModal: closeRestoreAPetModal,
    modalRef: petRestoreAPetRef
  } = useModal();

  const {
    isOpen: isCreatePetOpen,
    openModal: openCreatePetModal,
    closeModal: closeCreatePetModal,
    modalRef: CreatePetModalRef
  } = useModal();

  return (
    <>
      <Header type="logoAndProfile" />

      <main className="container flex flex-col items-center pt-10 px-3 ">
        <div className="flex w-full flex-col gap-5">
          <div className="flex w-full flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
            <div className="flex flex-col gap-2">
              <h1>Мои питомцы:</h1>
            </div>

            <div className="flex gap-x-4 items-center self-start">
              <Button
                size="small"
                className="conte"
                onClick={() => openRestoreAPetModal()}
              >
                Восстановить
              </Button>
              <button
                type="button"
                className="relative flex w-22 h-22 bg-brand-primary rounded-full justify-center items-center cursor-pointer"
                onClick={() => openCreatePetModal()}
              >
                <div className="absolute w-1/2 h-1 rounded-xl bg-white top-1/2 -translate-y-1/2"></div>
                <div className="absolute w-1/2 h-1 rounded-xl bg-white top-1/2 -translate-y-1/2 rotate-90"></div>
              </button>
            </div>
          </div>

          <div className="rounded-[28px] border border-black/5 bg-white/70 p-4 shadow-sm backdrop-blur-sm">
            <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
              <div>
                <h3>Вариант отображения</h3>
              </div>

              <div className="flex flex-wrap gap-2">
                {petCardViewOptions.map((option) => {
                  const isActive = cardView === option.value;

                  return (
                    <button
                      key={option.value}
                      type="button"
                      className={cn(
                        "flex justify-center min-w-34 rounded-2xl border px-4 py-3 text-left transition-all",
                        isActive
                          ? "border-brand-primary bg-brand-primary text-white shadow-md"
                          : "border-gray-200 bg-white text-brand-slate hover:border-brand-primary/40 hover:bg-brand-bg"
                      )}
                      onClick={() => setCardView(option.value)}
                    >
                      <span className="block text-sm font-semibold">{option.label}</span>
                    </button>
                  )
                })}
              </div>
            </div>
          </div>
        </div>
        {loadError && <p className="text-red-600 mt-4 w-full text-center">{loadError}</p>}
        <div
          className={cn(
            "mt-5 w-full",
            cardView === "compact"
              ? "flex flex-col gap-3"
              : "grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6"
          )}
        >
          {pets.map((pet: PetResponse) => (
            <PetCard
              key={pet.pet_id}
              pet={pet}
              view={cardView}
              onClick={() => navigate(`/pet/${pet.pet_id}`)}
            />
          ))}
        </div>
        {pets.length === 0 && !loadError && (
          <p className="mt-8 text-brand-wood text-center">Пока нет питомцев — добавьте первого.</p>
        )}
      </main>

      {isRestoreAPetOpen && (
        <RestoreAPet
          ref={petRestoreAPetRef}
          closeModal={closeRestoreAPetModal}
          onCreated={() => void loadPets()}
        />
      )}

      {isCreatePetOpen && (
        <CreatePetModal
          ref={CreatePetModalRef}
          closeModal={closeCreatePetModal}
          onCreated={() => void loadPets()}
        />
      )}
    </>
  )
}
