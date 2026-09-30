import { Header } from "@widgets/header";
import {Button} from "@shared/ui/Button.tsx";
import {cn} from "@shared/utils/utils.ts";
import {useCallback, useEffect, useRef, useState} from "react";
import {useNavigate, useParams} from "react-router";
import {
  petsApi,
  MedicalHistoryStatus,
  type MedicalEventResponse,
  type PetResponse,
  typeActionLabel,
} from "@entities/pet";
import { getApiErrorMessage } from "@shared/lib/apiError";
import { resolveMediaUrl } from "@shared/lib/imageUrl";
import { EditPetModal } from "@features/pet-edit/ui/EditPetModal";
import { MedicalEventModal } from "@features/medical-event/ui/MedicalEventModal";
import {MedicalHistoryCard} from "@shared/ui/Card.tsx";
import {useModal} from "@shared/hooks/useModal.ts";
import {useConfirmStore} from "@features/confirm/modal/confirm.store.ts";

type FilterTab = "planned" | "overdue" | "completed";

export const PetPage = () => {
  const { petId: petIdParam } = useParams<{ petId: string }>();
  const petId = Number(petIdParam);
  const navigate = useNavigate();

  const [pet, setPet] = useState<PetResponse | null>(null);
  const [events, setEvents] = useState<MedicalEventResponse[]>([]);
  const [totalEvents, setTotalEvents] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [tab, setTab] = useState<FilterTab>("planned");
  const [editingEvent, setEditingEvent] = useState<MedicalEventResponse | null>(null);
  const photoInputRef = useRef<HTMLInputElement>(null);

  const {
    isOpen: isPetEditOpen,
    openModal: openPetEditModal,
    closeModal: closePetEditModal,
    modalRef: petEditModalRef
  } = useModal();

  const {
    isOpen: isMedicalEventOpen,
    openModal: openMedicalEventModal,
    closeModal: closeMedicalEventModal,
    modalRef: medicalEventModalRef
  } = useModal();

  const load = useCallback(async () => {
    if (!Number.isFinite(petId)) return;
    try {
      setError(null);
      const [{ data: petData }, { data: history }] = await Promise.all([
        petsApi.getPet(petId),
        petsApi.getMedicalHistory(petId, { limit: 500, offset: 0 }),
      ]);
      setPet(petData);
      setEvents(history.events ?? []);
      setTotalEvents(history.total_events ?? history.events?.length ?? 0);
    } catch (e) {
      setError(getApiErrorMessage(e));
    }
  }, [petId]);

  useEffect(() => {
    void load();
  }, [load]);

  const filtered = events.filter((ev) => {
    if (tab === "planned") return ev.status === MedicalHistoryStatus.Planned;
    if (tab === "completed") return ev.status === MedicalHistoryStatus.Completed;
    return ev.status === MedicalHistoryStatus.Overdue;
  });

  const photoUrl = pet?.photo ? resolveMediaUrl(pet.photo) : undefined;

  const downloadBlob = (blob: Blob, filename: string) => {
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleExportPdf = async () => {
    try {
      const res = await petsApi.exportPdf(petId);
      downloadBlob(res.data, `pet-${petId}-history.pdf`);
    } catch (e) {
      setError(getApiErrorMessage(e));
    }
  };

  const handleExportIcs = async () => {
    try {
      const res = await petsApi.exportCalendar(petId);
      downloadBlob(res.data, `pet-${petId}-events.ics`);
    } catch (e) {
      setError(getApiErrorMessage(e));
    }
  };

  const openCreateMedical = () => {
    setEditingEvent(null);
    openMedicalEventModal();
  };

  const openEditMedical = (ev: MedicalEventResponse) => {
    setEditingEvent(ev);
    openMedicalEventModal();
  };

  const deleteEvent = async (ev: MedicalEventResponse) => {
    try {
      await petsApi.deleteMedicalEvent(petId, ev.medical_action_id);
      await load();
    } catch (e) {
      setError(getApiErrorMessage(e));
    }
  };

  const deletePet = () => {
    useConfirmStore.getState().open({
      message: "Удалить питомца?",
      okText: "Да",
      cancelText: "Нет",
      onCancel: () => {},
      onConfirm: async () => {
        try {
          await petsApi.deletePet(petId);
          navigate("/pets");
        } catch (e) {
          setError(getApiErrorMessage(e));
        }
      },
    })

  };

  const handleDeleteIcon = () => {
    useConfirmStore.getState().open({
      message: "Удалить аватарку?",
      okText: "Да",
      cancelText: "Нет",
      onCancel: () => {},
      onConfirm: () => {
        if (!pet?.pet_id) {
          console.warn("Pet ID не найден");
          return;
        }

        petsApi.deletePetPhoto(pet.pet_id)
          .then(() => void load())
          .catch(e => console.error(getApiErrorMessage(e)));
      }
    })
  }

  const handleUploadPhoto = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file || !pet?.pet_id) return;
    try {
      await petsApi.updatePhoto(pet.pet_id, file );
      await load();
    } catch (err) {
      setError(getApiErrorMessage(err));
    } finally {
      e.target.value = "";
    }
  };


  if (!Number.isFinite(petId)) {
    return (
      <>
        <Header type="logoAndProfile" />
        <main className="container mt-10">
          <p>Неверная ссылка</p>
        </main>
      </>
    );
  }

  return (
    <>
      <Header type="logoAndProfile" />

      <main className="container flex flex-col gap-6 mt-6 md:mt-10">
        <button
          type="button"
          className="inline-flex gap-1 self-start items-center cursor-pointer"
          onClick={() => navigate(-1)}
        >
          <svg className="w-5 h-4 rotate-180" viewBox="0 0 27 23" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M26.0607 12.1066C26.6464 11.5208 26.6464 10.571 26.0607 9.98524L16.5147 0.439297C15.9289 -0.14649 14.9792 -0.14649 14.3934 0.439297C13.8076 1.02508 13.8076 1.97483 14.3934 2.56062L22.8787 11.0459L14.3934 19.5312C13.8076 20.117 13.8076 21.0667 14.3934 21.6525C14.9792 22.2383 15.9289 22.2383 16.5147 21.6525L26.0607 12.1066ZM0 11.0459L0 12.5459H25V11.0459V9.5459H0L0 11.0459Z" fill="#F97316"/>
          </svg>
          <h3 className="text-brand-primary">Назад</h3>
        </button>

        {error && <p className="text-red-600">{error}</p>}

        <section className="flex flex-col lg:flex-row p-5 gap-6 md:p-8 bg-white rounded-2xl">
          <div className="flex flex-col sm:flex-row items-center sm:items-start gap-5 w-full">
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
                  src={photoUrl}
                  alt=""
                  className={`${photoUrl?.includes("pet-standart") ? 'w-2/3 h-2/3 m-auto' : 'w-full h-full'} object-cover`}
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
            <div className="text-center sm:text-left min-w-0">
              <div className="w-full max-w-65 sm:max-w-full lg:max-w-135 xl:max-w-180 flex justify-center sm:justify-start items-center gap-2">
                <h2 title={pet?.name ?? "…"} className="truncate">{pet?.name ?? "…"}</h2>
              </div>
              <div className="mt-2 space-y-1">
                <h3>Порода: {pet?.breed ?? "—"}</h3>
                <h3>Вес: {pet?.weight != null ? `${pet.weight} кг` : "—"}</h3>
                <h3>
                  Дата рождения:{" "}
                  {pet?.date_birth ? new Date(pet.date_birth).toLocaleDateString("ru-RU") : "—"}
                </h3>
                <h3>Окрас: {pet?.color ?? "—"}</h3>
              </div>
            </div>
          </div>
          <div className="flex flex-col gap-3 justify-between">
            <Button className="w-full lg:w-auto lg:self-start lg:ml-auto" type="button" onClick={() => openPetEditModal()}>
              Редактировать
            </Button>
            <Button className="w-full lg:w-auto lg:self-start lg:ml-auto lg:text-sm" intent="red" type="button" onClick={() => deletePet()}>
              Удалить питомца
            </Button>
          </div>
        </section>

        <section className="flex flex-col p-5 md:p-8 bg-white rounded-2xl gap-6 md:gap-10">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <h2>Медицинские события ({totalEvents}):</h2>
            <div className="flex flex-col sm:flex-row gap-3 w-full sm:w-auto">
              <Button type="button" className="flex items-center justify-center gap-2 w-full sm:w-auto" onClick={openCreateMedical}>
                <svg className="w-4 h-4" viewBox="0 0 26 26" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M23.9062 14.0625H1.40625C0.6375 14.0625 0 13.425 0 12.6562C0 11.8875 0.6375 11.25 1.40625 11.25H23.9062C24.675 11.25 25.3125 11.8875 25.3125 12.6562C25.3125 13.425 24.675 14.0625 23.9062 14.0625Z" fill="white"/>
                  <path d="M12.6562 25.3125C11.8875 25.3125 11.25 24.675 11.25 23.9062V1.40625C11.25 0.6375 11.8875 0 12.6562 0C13.425 0 14.0625 0.6375 14.0625 1.40625V23.9062C14.0625 24.675 13.425 25.3125 12.6562 25.3125Z" fill="white"/>
                </svg>
                Добавить
              </Button>
              <Button type="button" className="w-full sm:w-auto" onClick={handleExportPdf}>
                Документ (.pdf)
              </Button>
              <Button type="button" className="w-full sm:w-auto" onClick={handleExportIcs}>
                Календарь (.ics)
              </Button>
            </div>
          </div>
          <div>
            <div className="flex gap-6 sm:gap-10 overflow-x-auto">
              <button
                type="button"
                className={cn(
                  "transition-all duration-200 border-b-3 border-solid border-transparent whitespace-nowrap cursor-pointer pb-4",
                  tab === "planned" && "border-brand-slate",
                )}
                onClick={() => setTab("planned")}
              >
                <h3>Запланировано</h3>
              </button>
              <button
                type="button"
                className={cn(
                  "transition-all duration-200 border-b-3 border-solid border-transparent whitespace-nowrap cursor-pointer pb-4",
                  tab === "completed" && "border-brand-slate",
                )}
                onClick={() => setTab("completed")}
              >
                <h3>Завершено</h3>
              </button>
              <button
                type="button"
                className={cn(
                  "transition-all duration-200 border-b-3 border-solid border-transparent whitespace-nowrap cursor-pointer pb-4",
                  tab === "overdue" && "border-brand-slate",
                )}
                onClick={() => setTab("overdue")}
              >
                <h3>Просрочено</h3>
              </button>
            </div>
            <div className="w-full h-0.5 bg-brand-slate rounded" />
          </div>

          <div className="flex flex-col gap-3">
            {filtered.length === 0 && <p className="text-brand-wood">В этой вкладке пока нет записей.</p>}
            {filtered.map((ev) => (
              <div key={ev.medical_action_id} className="flex flex-col sm:flex-row sm:items-center gap-2 rounded-xl border border-gray-100 p-3">
                <div className="flex-1 min-w-0">
                  <MedicalHistoryCard>
                    {`${typeActionLabel(ev.type_action)} · ${new Date(ev.date).toLocaleString("ru-RU")}${
                      ev.description ? ` — ${ev.description}` : ""
                    }`}
                  </MedicalHistoryCard>
                </div>
                <div className="flex gap-2">
                  <Button type="button" size="small" onClick={() => openEditMedical(ev)}>
                    Изменить
                  </Button>
                  <Button type="button" intent="red" size="small" onClick={() => void deleteEvent(ev)}>
                    Удалить
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </section>
      </main>

      {isPetEditOpen && pet && (
        <EditPetModal
          ref={petEditModalRef}
          pet={pet}
          closeModal={closePetEditModal}
          onSaved={() => void load()}
        />
      )}

      {isMedicalEventOpen && (
        <MedicalEventModal
          ref={medicalEventModalRef}
          petId={petId}
          event={editingEvent}
          closeModal={() => {
            closeMedicalEventModal()
            setEditingEvent(null);
          }}
          onSaved={() => void load()}
        />
      )}


    </>
  );
};
