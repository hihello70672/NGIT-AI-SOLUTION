import { afterEach, describe, expect, it, vi } from 'vitest';
import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import App from './App';

afterEach(() => { cleanup(); localStorage.clear(); vi.restoreAllMocks(); });
const account = { id: 'u-1', email: 'alex@example.com', display_name: 'Alex Morgan', status: 'active', roles: ['user'], created_at: '2025-01-02T00:00:00Z' };
function json(data: unknown, status = 200) { return new Response(JSON.stringify(data), { status, headers: { 'Content-Type': 'application/json' } }); }
function mockFetch(impl: (url: string, init?: RequestInit) => Response | Promise<Response>) { return vi.spyOn(globalThis, 'fetch').mockImplementation(async (input, init) => impl(String(input), init)); }
async function signIn() { localStorage.setItem('ngit_access_token', 'token'); mockFetch(() => json(account)); render(<App />); await screen.findByRole('heading', { name: /good to have you here, alex/i }); }

describe('NGIT Brain and Agent workflows', () => {
 it('loads Brain models and sends a prompt to the Brain API', async () => {
  await signIn(); const requests: string[] = [];
  mockFetch(url => { requests.push(url); if (url.endsWith('/brain/models')) return json({ models: [{ model_id: 'local-1', model_name: 'Local model', capabilities: ['chat'], priority: 1 }] }); if (url.endsWith('/brain/generate')) return json({ text: 'A considered answer.', intent: 'general', confidence: .95, model_id: 'local-1', fallback_used: false }); return json(account); });
  fireEvent.click(screen.getByRole('button', { name: 'Brain chat' })); await screen.findByRole('option', { name: 'Local model' });
  fireEvent.change(screen.getByLabelText('Message NGIT Brain'), { target: { value: 'Help me think this through' } }); fireEvent.click(screen.getByRole('button', { name: 'Send message' }));
  expect(await screen.findByText('A considered answer.')).toBeInTheDocument(); expect(requests.some(url => url.endsWith('/brain/generate'))).toBe(true);
 });
 it('submits an Agent goal and explains the approval boundary for sensitive actions', async () => {
  await signIn(); const task = { task_id: 'task-2', goal: 'Send the report', state: 'awaiting_approval', observations: [{ state: 'approval_required', action: 'agent.tool.filesystem.write', resource_id: 'task-2:0' }] }; let submitted = false;
  mockFetch((url, init) => { if (url.endsWith('/agent/tasks?limit=50')) return json({ tasks: submitted ? [task] : [] }); if (url.endsWith('/agent/tasks') && init?.method === 'POST') { submitted = true; return json(task, 202); } if (url.endsWith('/agent/tasks/task-2')) return json(task); return json(account); });
  fireEvent.click(screen.getByRole('button', { name: 'Agent tasks' })); await screen.findByText('No tasks yet');
  fireEvent.change(screen.getByLabelText('Agent task goal'), { target: { value: 'Send the report' } }); fireEvent.click(screen.getByRole('button', { name: 'Submit goal' }));
  expect(await screen.findByText('Review required')).toBeInTheDocument(); expect(screen.getByText('agent.tool.filesystem.write')).toBeInTheDocument();
  expect(screen.getByText(/separate authorized reviewer/i)).toBeInTheDocument(); expect(screen.queryByRole('button', { name: 'Review and approve' })).not.toBeInTheDocument();
 });
});
