export interface User { id: string; email: string; display_name: string; status: string; roles: string[]; created_at: string }
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
    try { const body = await response.json() as ApiErrorPayload; message = body.error?.message || message; } catch { /* safe HTTP fallback */ }
    throw new Error(message);
  }
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}
const normalizeUser = (user: User): User => ({ ...user, roles: user.roles || [], created_at: user.created_at || '' });
export interface BrainModel { model_id: string; model_name: string; capabilities: string[]; priority: number }
export interface BrainResult { text: string; intent: string; confidence: number; model_id: string; fallback_used: boolean }
export interface BrainRequest { text: string; model_id?: string; temperature?: number; max_tokens?: number; min_confidence?: number; allow_fallback?: boolean }
export interface AgentTool { name: string; description?: string; sensitive?: boolean }
export interface AgentObservation { state: string; action?: string; resource_id?: string; message?: string; [key: string]: unknown }
export interface AgentTask { task_id: string; goal: string; state: string; observations: AgentObservation[]; pending_approval_id?: string | null; result?: unknown; error?: string | null; created_at?: string }
export interface AgentApproval { task_id: string; approval_id: string; action: string; resource_id: string; status: string }
export const api = {
  login: async (email: string, password: string): Promise<TokenResponse> => { const result = await request<TokenResponse>('/auth/login', { method: 'POST', body: JSON.stringify({ email, password }) }); return { ...result, user: normalizeUser(result.user) }; },
  register: async (display_name: string, email: string, password: string): Promise<TokenResponse> => { const result = await request<TokenResponse>('/auth/register', { method: 'POST', body: JSON.stringify({ display_name, email, password }) }); return { ...result, user: normalizeUser(result.user) }; },
  me: async (token: string): Promise<User> => normalizeUser(await request<User>('/users/me', {}, token)),
  updateMe: async (token: string, display_name: string): Promise<User> => normalizeUser(await request<User>('/users/me', { method: 'PATCH', body: JSON.stringify({ display_name }) }, token)),
  logout: (token: string): Promise<void> => request<void>('/auth/logout', { method: 'POST' }, token),
  adminUsers: async (token: string): Promise<User[]> => { const result = await request<{ users: User[] }>('/users?limit=100&offset=0', {}, token); return result.users.map(normalizeUser); },
  brainModels: (token: string) => request<{ models: BrainModel[] }>('/brain/models', {}, token),
  generate: (token: string, body: BrainRequest) => request<BrainResult>('/brain/generate', { method: 'POST', body: JSON.stringify(body) }, token),
  agentTools: (token: string) => request<{ tools: AgentTool[] }>('/agent/tools', {}, token),
  agentTasks: (token: string, limit = 50) => request<{ tasks: AgentTask[] }>(`/agent/tasks?limit=${limit}`, {}, token),
  agentTask: (token: string, taskId: string) => request<AgentTask>(`/agent/tasks/${encodeURIComponent(taskId)}`, {}, token),
  submitTask: (token: string, goal: string) => request<AgentTask>('/agent/tasks', { method: 'POST', body: JSON.stringify({ goal }) }, token),
  requestApproval: (token: string, taskId: string) => request<AgentApproval>(`/agent/tasks/${encodeURIComponent(taskId)}/approve`, { method: 'POST' }, token),
  decideApproval: (token: string, approvalId: string, approved: boolean) => request<{ approval_id: string; status: string }>(`/agent/approvals/${encodeURIComponent(approvalId)}/decision`, { method: 'POST', body: JSON.stringify({ approved }) }, token),
  resumeTask: (token: string, taskId: string, approvalId: string) => request<AgentTask>(`/agent/tasks/${encodeURIComponent(taskId)}/resume`, { method: 'POST', body: JSON.stringify({ approval_id: approvalId }) }, token),
  rejectTask: (token: string, taskId: string) => request<AgentTask>(`/agent/tasks/${encodeURIComponent(taskId)}/reject`, { method: 'POST' }, token),
};
export function getSavedToken(): string | null { try { return localStorage.getItem('ngit_access_token'); } catch { return null; } }
export function saveToken(token: string | null): void { try { if (token) localStorage.setItem('ngit_access_token', token); else localStorage.removeItem('ngit_access_token'); } catch { /* current tab session remains usable */ } }
