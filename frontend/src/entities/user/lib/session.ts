import { usersApi } from '../api/userApi';
import { useSessionStore } from '../model/session-store';

export async function loadSessionUser() {
  const session = useSessionStore.getState();
  session.setLoading(true);

  try {
    const { data } = await usersApi.getProfile();
    session.setUser(data);
    return data;
  } finally {
    session.setLoading(false);
  }
}
