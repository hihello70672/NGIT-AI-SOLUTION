export interface User {
  id: string; email: string; display_name: string; status: string; roles: string[]; created_at: string;
}
export interface TokenResponse { access_token: string; token_type?: string; user: User }
export interface ApiError { error?: { code?: string; message?: string; request_id?: string } }
const baseUrl = (import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000').replace(/\/$/, '');
const prefix = '/api/v1';

async function request<T>(path: string, options: RequestInit = {}, token?: string): Promise<T> {
  const headers = new Headers(options.headers);
  if (options.body) headers.set('Content-Type', 'application/json');
  if (token) headers.set('Authorization', `Bearer ${token}`);
  const response = await fetch(`${baseUrl}${prefix}${path}`, { ...options, headers });
  if (!response.ok) {
    let message = `Request failed (${response.status})`;
    try { const body = await response.json() as ApiError; message = body.error?.message || message; } catch { /* safe fallback */ }
    throw new Error(message);
  }
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}
export const api = {
  login: (email: string, password: string) => request<TokenResponse>('/auth/login', { method: 'POST', body: JSON.stringify({ email, password }) }),
  register: (display_name: string, email: string, password: string) => request<TokenResponse>('/auth/register', { method: 'POST', body: JSON.stringify({ display_name, email, password }) }),
  me: (token: string) => request<User>('/users/me', {}, token),
  updateMe: (token: string, display_name: string) => request<User>('/users/me', { method: 'PATCH', body: JSON.stringify({ display_name }) }, token),
  logout: (token: string) => request<void>('/auth/logout', { method: 'POST' }, token),
  adminUsers: (token: string) => request<User[]>('/admin/users', {}, token),
};
