export interface User {
  id: string; email: string; display_name: string; status: string; roles: string[]; created_at: string;
}
export interface TokenResponse { access_token: string; token_type?: string; user: User }
interface ApiErrorPayload { error?: { code?: string; message?: string; request_id?: string } }
const baseUrl = (import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000').replace(/\/$/, '');
const prefix = '/api/v1';
async function request<T>(path: string, options: RequestInit = {}, token?: string): Promise<T> {
  const headers = new Headers(options.headers);
  if (options.body) headers.set('Content-Type', 'application/json');
  if (token) headers.set('Authorization', `Bearer ${token}`);
  let response: Response;
  try { response = await fetch(`${baseUrl}${prefix}${path}`, { ...options, headers }); }
  catch { throw new Error('Unable to reach NGIT. Check that the API is running and try again.'); }
  if (!response.ok) {
    let message = `Request failed (${response.status})`;
    try { const body = await response.json() as ApiErrorPayload; message = body.error?.message || message; } catch { /* retain safe status message */ }
    throw new Error(message);
  }
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}
// FastAPI response models include user roles as a list; tolerate omitted optional fields safely.
const normalizeUser = (user: User): User => ({ ...user, roles: user.roles || [], created_at: user.created_at || '' });
export const api = {
  login: async (email: string, password: string) => { const r = await request<TokenResponse>('/auth/login', { method:'POST', body:JSON.stringify({email,password}) }); return { ...r, user:normalizeUser(r.user) }; },
  register: async (display_name: string, email: string, password: string) => { const r = await request<TokenResponse>('/auth/register', { method:'POST', body:JSON.stringify({display_name,email,password}) }); return { ...r, user:normalizeUser(r.user) }; },
  me: async (token: string) => normalizeUser(await request<User>('/users/me', {}, token)),
  updateMe: async (token: string, display_name: string) => normalizeUser(await request<User>('/users/me', { method:'PATCH', body:JSON.stringify({display_name}) }, token)),
  logout: (token: string) => request<void>('/auth/logout', { method:'POST' }, token),
  adminUsers: async (token: string) => (await request<User[]>('/admin/users', {}, token)).map(normalizeUser),
};
export function getSavedToken(): string | null { try { return localStorage.getItem('ngit_access_token'); } catch { return null; } }
export function saveToken(token: string | null): void { try { if (token) localStorage.setItem('ngit_access_token', token); else localStorage.removeItem('ngit_access_token'); } catch { /* session remains usable in memory */ } }
