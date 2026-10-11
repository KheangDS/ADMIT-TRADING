import axios from 'axios';
import { clearSession, session } from './session';
import type { AuthResponse } from './types';
export const API_BASE = (import.meta.env.VITE_API_BASE_URL || '/api/v1').replace(/\/$/, '');
export const api = axios.create({ baseURL: API_BASE, withCredentials: true, timeout: 30000 });
api.interceptors.request.use((config) => {
  config.headers.set('X-AgriTrade-Portal', 'admin');
  const method = (config.method || 'get').toLowerCase();
  if (!['get', 'head', 'options'].includes(method)) {
    const url = config.url || '';
    const isPublicAuth = url.endsWith('/auth/login') || url.endsWith('/auth/register');
    if (!isPublicAuth && !session.csrf_token) {
      throw new Error(
        'Session CSRF token is unavailable. Reload your session before making changes.',
      );
    }
    if (session.csrf_token) {
      config.headers.set('X-CSRF-Token', session.csrf_token);
    }
  }
  return config;
});
let refreshingPromise: Promise<AuthResponse | null> | null = null;

export async function refreshAuthSession(): Promise<AuthResponse | null> {
  if (refreshingPromise) return refreshingPromise;
  refreshingPromise = (async () => {
    try {
      let data: AuthResponse;
      if (session.csrf_token) {
        try {
          const res = await api.post<AuthResponse>('/auth/refresh');
          data = res.data;
        } catch {
          const res = await api.get<AuthResponse>('/auth/me');
          data = res.data;
        }
      } else {
        const res = await api.get<AuthResponse>('/auth/me');
        data = res.data;
      }
      if (data.user && (data.user.role === 'admin' || data.user.role === 'superadmin')) {
        Object.assign(session, data);
        session.denied = false;
        session.ready = true;
        return data;
      } else {
        clearSession();
        session.denied = !!data.user && data.user.role !== 'admin' && data.user.role !== 'superadmin';
        return null;
      }
    } catch {
      clearSession();
      return null;
    } finally {
      refreshingPromise = null;
    }
  })();
  return refreshingPromise;
}

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const config = error.config;
    const status = error.response?.status;
    const url = config?.url || '';

    const isAuthEndpoint =
      url.endsWith('/auth/login') ||
      url.endsWith('/auth/refresh') ||
      url.endsWith('/auth/me') ||
      url.endsWith('/auth/logout');

    if (status === 401) {
      if (isAuthEndpoint || config?._retry) {
        clearSession();
        return Promise.reject(error);
      }

      config._retry = true;
      const auth = await refreshAuthSession();
      if (auth && auth.user && (auth.user.role === 'admin' || auth.user.role === 'superadmin')) {
        const method = (config.method || 'get').toLowerCase();
        if (!['get', 'head', 'options'].includes(method) && auth.csrf_token) {
          config.headers.set('X-CSRF-Token', auth.csrf_token);
        }
        return api(config);
      } else {
        clearSession();
        return Promise.reject(error);
      }
    }

    if (status === 403) {
      const detail = error.response?.data?.detail;
      if (
        (typeof detail === 'string' && detail.toLowerCase().includes('admin')) ||
        (session.user && session.user.role !== 'admin' && session.user.role !== 'superadmin')
      ) {
        session.denied = true;
      }
    }
    return Promise.reject(error);
  },
);
export function errorText(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail;
    const message =
      typeof detail === 'string' ? detail : detail ? JSON.stringify(detail) : error.message;
    return `${error.response ? `HTTP ${error.response.status}: ` : ''}${message}${!error.response ? ' — Check backend connectivity and deployment configuration.' : ''}`;
  }
  return error instanceof Error ? error.message : String(error);
}
let bootstrapping: Promise<void> | null = null;
export function bootstrap(): Promise<void> {
  if (bootstrapping) return bootstrapping;
  bootstrapping = (async () => {
    session.error = '';
    session.denied = false;
    try {
      const { data } = await api.get<AuthResponse>('/auth/me');
      Object.assign(session, data);
      session.denied = !!data.user && data.user.role !== 'admin' && data.user.role !== 'superadmin';
    } catch (error) {
      clearSession();
      session.error = errorText(error);
    } finally {
      session.ready = true;
      bootstrapping = null;
    }
  })();
  return bootstrapping;
}
export function loginUrl() {
  // Backend recognizes this safe sentinel and redirects only to configured ADMIN_URL.
  return `${API_BASE}/auth/google/start?return_to=/admin`;
}
export async function loginWithPassword(email: string, password: string): Promise<AuthResponse> {
  const { data } = await api.post<AuthResponse>('/auth/login', { email, password });
  Object.assign(session, data);
  session.ready = true;
  session.denied = !data.user || (data.user.role !== 'admin' && data.user.role !== 'superadmin');
  return data;
}
export async function download(path: string, filename: string) {
  const { data } = await api.get<Blob>(path, { responseType: 'blob' });
  const url = URL.createObjectURL(data);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  link.click();
  window.setTimeout(() => URL.revokeObjectURL(url), 1000);
}
export async function blobError(error: unknown) {
  if (axios.isAxiosError(error) && error.response?.data instanceof Blob) {
    try {
      const data = JSON.parse(await error.response.data.text());
      error.response.data = data;
    } catch {
      /* Retain HTTP error if non-JSON. */
    }
  }
  return errorText(error);
}
