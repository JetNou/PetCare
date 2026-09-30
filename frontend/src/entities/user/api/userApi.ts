import { api } from '@shared/api/axiosInstance';
import type { UserProfile, UpdateProfileDto } from '../model/types';

export const usersApi = {
  getProfile: () => api.get<UserProfile>('/users/'),

  updateProfile: (data: UpdateProfileDto) => {
    const formData = new FormData();

    if (data.user_login) formData.append('user_login', data.user_login);
    if (data.user_full_name) formData.append('user_full_name', data.user_full_name);
    if (data.user_email) formData.append('user_email', data.user_email);
    if (data.photo instanceof File) {
      formData.append('photo', data.photo);
    }

    return api.patch<UserProfile>('/users/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },

  deleteAvatar: () => api.delete('/users/avatar'),

  deleteProfile: () => api.delete('/users/'),

  restoreProfile: (token: string) =>
    api.post('/users/restore', null, { params: { token } }),

  getUserById: (userId: number) => api.get<UserProfile>(`/users/${userId}`),
};
