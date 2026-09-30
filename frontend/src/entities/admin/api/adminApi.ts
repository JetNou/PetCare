import { api } from '@shared/api/axiosInstance';
import type { PetResponse, UpdatePetDto } from '@entities/pet/model/types';
import type { UpdateProfileDto, UserProfile } from '@entities/user/model/types';
import type { SystemStatistics } from '../model/types';

export interface AdminSearchParams {
  user_login?: string | null;
  user_full_name?: string | null;
  user_email?: string | null;
  role_id?: number | null;
  limit?: number;
  offset?: number;
}

export const adminApi = {
  getStatistics: () => api.get<SystemStatistics>('/admin/statistics'),

  searchUsers: (params: AdminSearchParams) =>
    api.get<UserProfile[]>('/admin/users/all', { params }),

  updateUser: (userId: number, data: Pick<UpdateProfileDto, 'user_login' | 'user_full_name' | 'user_email'>) => {
    const payload = Object.fromEntries(
      Object.entries(data).filter(([, value]) => value !== undefined),
    );

    return api.patch(`/admin/user/${userId}/update`, payload);
  },

  deleteUser: (userId: number) => api.delete(`/admin/user/${userId}/delete`),

  resetUserAvatar: (userId: number) => api.patch(`/admin/user/${userId}/avatar`),

  getAllPets: () => api.get<PetResponse[]>('/admin/pets/all'),

  updatePet: (petId: number, data: UpdatePetDto) => {
    const payload = Object.fromEntries(
      Object.entries(data).filter(([key, value]) => key !== 'photo' && value !== undefined),
    );

    return api.patch(`/admin/pet/${petId}/update`, payload);
  },

  deletePet: (petId: number) => api.delete(`/admin/pet/${petId}/delete`),

  resetPetAvatar: (petId: number) => api.patch(`/admin/pet/${petId}/avatar`),

  getUserLogs: (userId: number, limit = 50) =>
    api.get<string[]>(`/admin/user/${userId}/logs`, { params: { limit } }),
};
