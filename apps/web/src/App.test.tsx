import { afterEach, describe, expect, it, vi } from 'vitest';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import App from './App';

afterEach(() => { cleanup(); localStorage.clear(); vi.restoreAllMocks(); });
const account = { id: 'u-1', email: 'alex@example.com', display_name: 'Alex Morgan', status: 'active', roles: ['user'], created_at: '2025-01-02T00:00:00Z' };
function json(data: unknown, status = 200) { return new Response(status === 204 ? null : JSON.stringify(data), { status, headers: { 'Content-Type': 'application/json' } }); }
function queueFetch(...results: Response[]) { return vi.spyOn(globalThis, 'fetch').mockImplementation(async () => results.shift() ?? json({})); }
async function signedIn() { localStorage.setItem('ngit_access_token', 'token'); queueFetch(json(account)); render(<App />); await screen.findByRole('heading', { name: /good to have you here, alex/i }); }

describe('NGIT web application', () => {
 it('loads Brain models, sends prompts through its API, and renders response metadata', async () => {
  await signedIn(); const fetchSpy = vi.spyOn(globalThis, 'fetch');
  // Replace the session fetch spy with a queue for models and generation.
  fetchSpy.mockImplementationOnce(async () => json({ models: [{ model_id: 'local-1', model_name: 'Local model', capabilities: ['chat'], priority: 1 }] })).mockImplementationOnce(async () => json({ text: 'A considered answer.', intent: 'general', confidence: .95, model_id: 'local-1', fallback_used: false }));
  fireEvent.click(screen.getByRole('button', { name: 'Brain chat' }));
  await screen.findByRole('option', { name: 'Local model' });
  fireEvent.change(screen.getByLabelText('Message NGIT Brain'), { target: { value: 'Help me think this through' } });
  fireEvent.click(screen.getByRole('button', { name: 'Send message' }));
  expect(await screen.findByText('A considered answer.')).toBeInTheDocument();
  expect(fetchSpy.mock.calls.at(-1)?.[0]).toContain('/brain/generate');
 });
 it('loads and submits Agent tasks and clearly protects approval decisions', async () => {
  await signedIn(); const fetchSpy = vi.spyOn(globalThis, 'fetch');
  fetchSpy.mockImplementationOnce(async () => json({ tasks: [] })).mockImplementationOnce(async () => json({ task_id: 'task-2', goal: 'Send the report', state: 'awaiting_approval', observations: [{ state: 'approval_required', action: 'agent.tool.filesystem.write', resource_id: 'task-2:0' }] }, 202)).mockImplementationOnce(async () => json({ tasks: [{ task_id: 'task-2', goal: 'Send the report', state: 'awaiting_approval', observations: [{ state: 'approval_required', action: 'agent.tool.filesystem.write', resource_id: 'task-2:0' }] }] })).mockImplementationOnce(async () => json({ task_id: 'task-2', goal: 'Send the report', state: 'awaiting_approval', observations: [{ state: 'approval_required', action: 'agent.tool.filesystem.write', resource_id: 'task-2:0' }] }));
  fireEvent.click(screen.getByRole('button', { name: 'Agent tasks' })); await screen.findByText('No tasks yet');
  fireEvent.change(screen.getByLabelText('Agent task goal'), { target: { value: 'Send the report' } }); fireEvent.click(screen.getByRole('button', { name: 'Submit goal' }));
  expect(await screen.findByText('Review required')).toBeInTheDocument();
  expect(screen.getByText('agent.tool.filesystem.write')).toBeInTheDocument();
  expect(screen.getByText(/separate authorized reviewer/i)).toBeInTheDocument();
  expect(screen.queryByRole('button', { name: 'Review and approve' })).not.toBeInTheDocument();
  expect(fetchSpy.mock.calls.some(call => String(call[0]).includes('/agent/tasks'))).toBe(true);
 });
});
