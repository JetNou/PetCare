import { api } from '@shared/api/axiosInstance.ts';
import type {
  UserCreate,
  UserLogin,
  TokenResponse,
  RefreshTokenRequest,
  ResetPasswordConfirm,
} from '@entities/user';

export const authApi = {
  register: (data: UserCreate) =>
    api.post<TokenResponse>('/auth/register', data),

  verifyEmail: (token: string) =>
    api.get<TokenResponse>('/auth/verify-email', { params: { token } }),

  resendVerification: () =>
    api.post('/auth/resend-verification'),

  resendVerificationByEmail: (userEmail: string) =>
    api.post('/auth/resend-verification-by-email', { user_email: userEmail }),

  login: (data: UserLogin) =>
    api.post<TokenResponse>('/auth/login', data),

  refresh: (data: RefreshTokenRequest) =>
    api.post<TokenResponse>('/auth/refresh', data),

  logout: () => api.post('/auth/logout'),

  requestPasswordReset: () => api.post('/users/reset-password/request'),

  confirmPasswordReset: (data: ResetPasswordConfirm) =>
    api.post('/users/reset-password/confirm', data),
};