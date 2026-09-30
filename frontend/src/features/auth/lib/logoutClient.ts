import { authApi } from '@features/auth/api/auth.api.ts';
import { setAccessToken } from '@shared/api/axiosInstance';
import { useSessionStore } from '@entities/user';

export async function logoutClient() {
  try {
    await authApi.logout();
  } catch {

  } finally {
    setAccessToken(null);
    localStorage.removeItem('refresh_token');
    useSessionStore.getState().setUser(null);
  }
}
