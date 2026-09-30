import { api } from '@shared/api/axiosInstance';
import type {
  PetCreate,
  PetResponse,
  UpdatePetDto,
  MedicalEventCreate,
  MedicalEventResponse,
  MedicalHistoryResponse,
  UpdateMedicalEventDto,
} from '../model/types';

export const petsApi = {
  getMyPets: () => api.get<PetResponse[]>('/pets/'),

  getPet: (petId: number) => api.get<PetResponse>(`/pets/${petId}`),

  createPet: (data: PetCreate) => api.post<PetResponse>('/pets/', data),

  updatePet: (petId: number, data: UpdatePetDto) => {
    const payload = Object.fromEntries(
      Object.entries(data).filter(([key, value]) => key !== 'photo' && value !== undefined),
    );

    return api.patch<PetResponse>(`/pets/${petId}`, payload);
  },

  updatePhoto: (petId: number, photo: File) => {
    const formData = new FormData();
    formData.append('photo', photo);

    return api.patch<PetResponse>(`/pets/${petId}/photo`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  },

  deletePet: (petId: number) => api.delete(`/pets/${petId}`),

  deletePetPhoto: (petId: number) => api.delete(`/pets/${petId}/photo`),

  restorePet: (token: string) =>
    api.post('/pets/restore', null, { params: { token } }),

  getMedicalHistory: (
    petId: number,
    params?: { status?: string | null; limit?: number; offset?: number },
  ) =>
    api.get<MedicalHistoryResponse>(`/pets/${petId}/medical_events`, { params }),

  getMedicalEvent: (petId: number, eventId: number) =>
    api.get<MedicalEventResponse>(`/pets/${petId}/medical_events/${eventId}`),

  createMedicalEvent: (petId: number, data: MedicalEventCreate) =>
    api.post<MedicalEventResponse>(`/pets/${petId}/medical_events`, data),

  updateMedicalEvent: (petId: number, eventId: number, data: UpdateMedicalEventDto) => {
    const payload = Object.fromEntries(
      Object.entries(data).filter(([, value]) => value !== undefined),
    );

    return api.patch<MedicalEventResponse>(
      `/pets/${petId}/medical_events/${eventId}`,
      payload,
    );
  },

  deleteMedicalEvent: (petId: number, eventId: number) =>
    api.delete(`/pets/${petId}/medical_events/${eventId}`),

  exportPdf: (petId: number) =>
    api.get(`/pets/${petId}/export/pdf`, { responseType: 'blob' }),

  exportCalendar: (petId: number) =>
    api.get(`/pets/${petId}/export/calendar`, { responseType: 'blob' }),
};
