import type {
  SQLInjectionResponse,
  SubscribeResponse,
  VulnerableLabInfo,
  CommandInjectionResponse,
} from '../types/vulnerable';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';
const BASE = `${API_BASE_URL}/api/v1/vulnerable`;

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const err = await res.json().catch(() => null);
    throw new Error(err?.detail || err?.message || `Lỗi server (${res.status})`);
  }
  return res.json();
}

/** Lấy thông tin tổng quan về Vulnerable Lab */
export async function getVulnerableLabInfo(): Promise<VulnerableLabInfo> {
  const res = await fetch(`${BASE}/info`);
  return handleResponse<VulnerableLabInfo>(res);
}

/** SQL Injection – Đăng ký customer bằng raw SQL concatenation */
export async function sqlInjectionRegister(
  customerName: string,
  email: string,
  segment?: string,
  city?: string,
): Promise<SQLInjectionResponse> {
  const res = await fetch(`${BASE}/sql-injection/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      customer_name: customerName,
      email,
      segment: segment ?? 'Consumer',
      city: city ?? 'Demo City',
    }),
  });
  return handleResponse<SQLInjectionResponse>(res);
}

/** SQL Injection – Tìm kiếm customer bằng raw LIKE query */
export async function sqlInjectionSearch(
  searchTerm: string,
): Promise<SQLInjectionResponse> {
  const res = await fetch(`${BASE}/sql-injection/search`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ search_term: searchTerm }),
  });
  return handleResponse<SQLInjectionResponse>(res);
}

/** LLM API Exploitation – Newsletter subscription (prompt injection demo) */
export async function llmSubscribe(
  name: string,
  email: string,
  message: string,
): Promise<SubscribeResponse> {
  const res = await fetch(`${BASE}/llm-api/subscribe`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name, email, message }),
  });
  return handleResponse<SubscribeResponse>(res);
}

/** OS Command Injection via LLM Tool Call (PortSwigger style) */
export async function osCommandInjection(
  userMessage: string,
  exploitServer?: string,
): Promise<CommandInjectionResponse> {
  const res = await fetch(`${BASE}/llm-api/os-command-injection`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      user_message: userMessage,
      exploit_server: exploitServer ?? '',
    }),
  });
  return handleResponse<CommandInjectionResponse>(res);
}
