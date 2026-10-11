import axios from 'axios';
import type { DashboardPayload } from '../types/dataset';
import type { AuthMetadata, Plan, Payment, Receipt, MemberDocument } from '../types/membership';
import { clearPrivateState } from './privateState';

export const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || '/api/v1').replace(/\/$/, '');
let csrfToken: string | null = null;
export function setCsrfToken(token: string | null) { csrfToken = token; }
export const apiClient = axios.create({ baseURL: API_BASE_URL, withCredentials: true });
apiClient.interceptors.request.use(config => {
  if (!['get', 'head', 'options'].includes(config.method || 'get') && csrfToken) {
    config.headers.set('X-CSRF-Token', csrfToken);
  }
  return config;
});
let refreshingPromise: Promise<AuthMetadata | null> | null = null;

export async function refreshSession(): Promise<AuthMetadata | null> {
  if (refreshingPromise) return refreshingPromise;
  refreshingPromise = (async () => {
    try {
      let data: AuthMetadata;
      if (csrfToken) {
        try {
          const res = await apiClient.post<AuthMetadata>('/auth/refresh');
          data = res.data;
        } catch {
          const res = await apiClient.get<AuthMetadata>('/auth/me');
          data = res.data;
        }
      } else {
        const res = await apiClient.get<AuthMetadata>('/auth/me');
        data = res.data;
      }
      if (data.user) {
        setCsrfToken(data.csrf_token);
        return data;
      } else {
        setCsrfToken(null);
        clearPrivateState(401);
        return null;
      }
    } catch {
      setCsrfToken(null);
      clearPrivateState(401);
      return null;
    } finally {
      refreshingPromise = null;
    }
  })();
  return refreshingPromise;
}

apiClient.interceptors.response.use(
  response => response,
  async error => {
    const config = error.config;
    const status = error.response?.status;
    const url = config?.url || '';

    const isAuthEndpoint =
      url.endsWith('/auth/login') ||
      url.endsWith('/auth/register') ||
      url.endsWith('/auth/refresh') ||
      url.endsWith('/auth/me') ||
      url.endsWith('/auth/logout');

    const isLoginOrRegister = url.endsWith('/auth/login') || url.endsWith('/auth/register');

    if (status === 401) {
      if (isLoginOrRegister) {
        return Promise.reject(error);
      }

      if (isAuthEndpoint || config?._retry) {
        csrfToken = null;
        clearPrivateState(401);
        return Promise.reject(error);
      }

      config._retry = true;
      const metadata = await refreshSession();
      if (metadata && metadata.user) {
        const method = (config.method || 'get').toLowerCase();
        if (!['get', 'head', 'options'].includes(method) && metadata.csrf_token) {
          config.headers.set('X-CSRF-Token', metadata.csrf_token);
        }
        return apiClient(config);
      } else {
        csrfToken = null;
        clearPrivateState(401);
        return Promise.reject(error);
      }
    }

    if (status === 403) {
      clearPrivateState(403);
    }

    return Promise.reject(error);
  },
);
export function apiError(error: unknown, fallback = 'Request failed. Please try again.'): string {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail;
    if (typeof detail === 'string') return detail;
    if (!error.response) return 'Cannot reach the service. Check your connection and try again.';
    if (error.response.status === 401) return 'Your session has expired. Please sign in again.';
    if (error.response.status === 403) return 'Access is unavailable. Check your membership in Account.';
  }
  return fallback;
}
export const getAuth = async () => (await apiClient.get<AuthMetadata>('/auth/me')).data;
export const logout = async () => { await apiClient.post('/auth/logout'); };
export const registerWithPassword = async (name: string, email: string, password: string) => {
  const data = (await apiClient.post<AuthMetadata>('/auth/register', { name, email, password })).data;
  setCsrfToken(data.csrf_token);
  return data;
};
export const loginWithPassword = async (email: string, password: string) => {
  const data = (await apiClient.post<AuthMetadata>('/auth/login', { email, password })).data;
  setCsrfToken(data.csrf_token);
  return data;
};
export const forgotPasswordApi = async (email: string) =>
  (await apiClient.post<{ message: string }>('/auth/forgot-password', { email })).data;
export const resetPasswordApi = async (token: string, password: string) =>
  (await apiClient.post<{ message: string }>('/auth/reset-password', { token, password })).data;
export function googleSignInUrl(returnTo = '/account') {
  const safe = returnTo.startsWith('/') && !returnTo.startsWith('//') && !returnTo.includes('\\') ? returnTo : '/account';
  return `${API_BASE_URL}/auth/google/start?return_to=${encodeURIComponent(safe)}`;
}
export const getPlans = async () => (await apiClient.get<Plan[]>('/plans')).data;
export const getPayments = async () => (await apiClient.get<Payment[]>('/payments')).data;
export const createPayment = async (planId: string, payerName: string) =>
  (await apiClient.post<Payment>('/payments', { plan_id: planId, payer_name: payerName })).data;
export const confirmPayment = async (id: string) => (await apiClient.post<Payment>(`/payments/${encodeURIComponent(id)}/confirm`, {})).data;
export const reportPaymentDelay = async (id: string, message?: string) =>
  (await apiClient.post<Payment>(`/payments/${encodeURIComponent(id)}/delay-report`, { message: message || undefined })).data;
export const getReceipts = async () => (await apiClient.get<Receipt[]>('/receipts')).data;
export const getDocuments = async () => (await apiClient.get<MemberDocument[]>('/documents')).data;
export async function privateBlob(path: string) {
  return (await apiClient.get<Blob>(path, { responseType: 'blob' })).data;
}
export async function fetchCurrentAnalytics(exchangeRate?: number): Promise<DashboardPayload> {
  return (await apiClient.get<DashboardPayload>('/analytics/current', { params: exchangeRate ? { exchange_rate: exchangeRate } : {} })).data;
}
export async function recalculateAnalytics(_sessionId: string, exchangeRate: number): Promise<DashboardPayload> {
  return (await apiClient.post<DashboardPayload>('/analytics/recalculate', { exchange_rate: exchangeRate })).data;
}
export function isPublicationChanged(error: unknown): boolean {
  return axios.isAxiosError(error) && error.response?.status === 409 && error.response?.data?.detail?.code === 'publication_changed';
}
export async function sendChatMessage(_sessionId: string, question: string, exchangeRate: number, publicationId?: string | null) {
  return (await apiClient.post('/chat', { question, exchange_rate: exchangeRate, publication_id: publicationId ?? null })).data;
}
export interface PublicTradeStatus {
  current_revision_id: string | null;
  destination_countries_count: number;
  total_commodities_count: number;
  total_records: number;
  hs4_chapters_count: number;
  reporting_period: string;
}
export const getTradeStatus = async () => (await apiClient.get<PublicTradeStatus>('/trade/status')).data;
