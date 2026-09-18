import axios from 'axios';
import type { DashboardPayload } from '../types/dataset';

const API_BASE_URL = 'http://localhost:8000/api/v1';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export async function fetchCurrentAnalytics(exchangeRate?: number): Promise<DashboardPayload> {
  const params: Record<string, any> = {};
  if (exchangeRate && exchangeRate > 0) {
    params.exchange_rate = exchangeRate;
  }
  const response = await apiClient.get<DashboardPayload>('/analytics/current', { params });
  return response.data;
}

export async function uploadDataset(file: File, exchangeRate: number = 4000): Promise<DashboardPayload> {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('exchange_rate', exchangeRate.toString());

  const response = await axios.post<DashboardPayload>(`${API_BASE_URL}/upload`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
}

export async function recalculateAnalytics(sessionId: string, exchangeRate: number): Promise<DashboardPayload> {
  const response = await apiClient.post<DashboardPayload>('/analytics/recalculate', {
    session_id: sessionId,
    exchange_rate: exchangeRate,
  });
  return response.data;
}

export async function sendChatMessage(sessionId: string, question: string, exchangeRate: number) {
  const response = await apiClient.post('/chat', {
    session_id: sessionId,
    question,
    exchange_rate: exchangeRate,
  });
  return response.data;
}
