import type { ChatResponse, HealthCheckResponse } from '../types/chat';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';

export async function askQuestion(
  question: string,
  sessionId?: string,
  includeSql: boolean = true
): Promise<ChatResponse> {
  const response = await fetch(`${API_BASE_URL}/api/v1/chat/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      question,
      session_id: sessionId,
      include_sql: includeSql,
      include_raw_data: false,
    }),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => null);
    const errorMessage =
      errorData?.detail || errorData?.message || `Lỗi server (${response.status})`;
    throw new Error(errorMessage);
  }

  return response.json();
}

export async function checkBackendHealth(): Promise<HealthCheckResponse> {
  const response = await fetch(`${API_BASE_URL}/health`, {
    method: 'GET',
    headers: {
      'Accept': 'application/json',
    },
  });

  if (!response.ok) {
    throw new Error('Backend không khả dụng');
  }

  return response.json();
}
