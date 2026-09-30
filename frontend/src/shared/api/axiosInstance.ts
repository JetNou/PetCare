import axios, { AxiosError } from 'axios';

let accessToken: string | null = null;

export const setAccessToken = (token: string | null) => {
  accessToken = token;
};
export const getAccessToken = () => accessToken;

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL ?? 'http://localhost:8000',
  headers: { 'Content-Type': 'application/json' },
  withCredentials: true,
});

// ── Request ───
api.interceptors.request.use((config) => {
  if (accessToken) {
    config.headers.Authorization = `Bearer ${accessToken}`;
  }
  return config;
});


// ── Response ───
let isRefreshing = false;
let failedQueue: Array<{
  resolve: (token: string | null) => void;
  reject: (err: unknown) => void;
}> = [];

const processQueue = (error: unknown, token: string | null) => {
  failedQueue.forEach((p) => {
    if (error) p.reject(error);
    else p.resolve(token);
  });
  failedQueue = [];
};

api.interceptors.response.use(
  (response) => {
    if (
      response.data?.error &&
      response.data?.error.code === 200 &&
      response.data?.error.message === "Пользователи не найдены"
    ) {
      return {
        ...response,
        data: []
      }
    }

    return  response
  },
  async (error: AxiosError) => {
    const originalRequest = error.config as typeof error.config & {
      _retry?: boolean;
    };

    if (error.response?.status === 403 && !originalRequest._retry && !error.config?.url?.includes("/auth/login")) {
      if (isRefreshing) {
        return new Promise<string | null>((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        }).then((token) => {
          if (token && originalRequest.headers) {
            originalRequest.headers.Authorization = `Bearer ${token}`;
          } else if (originalRequest.headers) {
            delete originalRequest.headers.Authorization;
          }
          return api(originalRequest);
        });
      }

      originalRequest._retry = true;
      isRefreshing = true;

      try {
        const refreshToken = localStorage.getItem('refresh_token');
        if (!refreshToken) throw new Error('No refresh token');

        const refreshUrl = `${api.defaults.baseURL?.replace(/\/$/, '')}/auth/refresh`;
        const { data } = await axios.post<{ refresh_token: string }>(
          refreshUrl,
          { refresh_token: refreshToken },
          { withCredentials: true },
        );

        localStorage.setItem('refresh_token', data.refresh_token);

        processQueue(null, getAccessToken());
        if (originalRequest.headers) {
          delete originalRequest.headers.Authorization;
        }
        return api(originalRequest);
      } catch (refreshError) {
        processQueue(refreshError, null);
        setAccessToken(null);
        localStorage.removeItem('refresh_token');
        window.location.href = '/login';
        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }

    return Promise.reject(error);
  },
);