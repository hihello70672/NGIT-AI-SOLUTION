import { afterEach, describe, expect, it, vi } from 'vitest';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import App from './App';

afterEach(() => { cleanup(); localStorage.clear(); vi.restoreAllMocks(); });
const account = { id:'u-1', email:'alex@example.com', display_name:'Alex Morgan', status:'active', roles:['user'], created_at:'2025-01-02T00:00:00Z' };
function json(data: unknown, status = 200) { return new Response(status === 204 ? null : JSON.stringify(data), { status, headers:{ 'Content-Type':'application/json' } }); }
function queueFetch(...results: Response[]) { return vi.spyOn(globalThis,'fetch').mockImplementation(async () => results.shift() ?? json({})); }
async function signedIn(role = 'user') { localStorage.setItem('ngit_access_token','token'); queueFetch(json({ ...account, roles:[role] })); render(<App/>); await screen.findByRole('heading',{name:/Good to have you here, Alex/i}); }

describe('NGIT web application', () => {
  it('shows login and communicates safe authentication errors accessibly', async () => {
    queueFetch(json({error:{message:'Email or password is incorrect'}} ,401)); render(<App/>);
    fireEvent.change(screen.getByLabelText('Email address'),{target:{value:'alex@example.com'}}); fireEvent.change(screen.getByLabelText('Password'),{target:{value:'wrong-pass'}}); fireEvent.click(screen.getByRole('button',{name:/sign in/i}));
    expect(await screen.findByRole('alert')).toHaveTextContent('Email or password is incorrect');
  });
  it('toggles registration form and submits account creation', async () => {
    const fetchSpy=queueFetch(json({access_token:'new-token',user:account})); render(<App/>); fireEvent.click(screen.getByRole('button',{name:'Create an account'}));
    expect(screen.getByLabelText('Your name')).toBeInTheDocument(); fireEvent.change(screen.getByLabelText('Your name'),{target:{value:'Alex Morgan'}}); fireEvent.change(screen.getByLabelText('Email address'),{target:{value:'alex@example.com'}}); fireEvent.change(screen.getByLabelText('Password'),{target:{value:'secure-password-123'}}); fireEvent.click(screen.getByRole('button',{name:/create account/i}));
    await screen.findByRole('heading',{name:/Good to have you here, Alex/i}); expect(fetchSpy.mock.calls[0][1]?.body).toContain('display_name');
  });
  it('navigates dashboard feature cards into profile and agent screens', async () => {
    await signedIn(); fireEvent.click(screen.getByRole('button',{name:/your account/i})); expect(await screen.findByRole('heading',{name:'Profile settings'})).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button',{name:/overview/i})); fireEvent.click(screen.getByRole('button',{name:/personal agent/i})); expect(await screen.findByRole('heading',{name:/make progress, thoughtfully/i})).toBeInTheDocument();
  });
  it('loads Brain models and submits a chat prompt using the existing API', async () => {
    await signedIn(); const spy=vi.spyOn(globalThis,'fetch').mockResolvedValueOnce(json({models:[{model_id:'local-1',model_name:'Local model',capabilities:['chat'],priority:1}]})).mockResolvedValueOnce(json({text:'A considered answer.',intent:'general',confidence:.95,model_id:'local-1',fallback_used:false}));
    fireEvent.click(screen.getByRole('button',{name:'Brain chat'})); await screen.findByRole('option',{name:'Local model'}); fireEvent.change(screen.getByLabelText('Message NGIT Brain'),{target:{value:'Help me think this through'}}); fireEvent.click(screen.getByRole('button',{name:'Send message'})); expect(await screen.findByText('A considered answer.')).toBeInTheDocument(); expect(spy).toHaveBeenCalledTimes(2);
  });
  it('shows Brain model load errors', async () => { await signedIn(); vi.spyOn(globalThis,'fetch').mockResolvedValueOnce(json({error:{message:'Brain runtime unavailable'}},503)); fireEvent.click(screen.getByRole('button',{name:'Brain chat'})); expect(await screen.findByRole('alert')).toHaveTextContent('Brain runtime unavailable'); });
  it('creates an Agent task, refreshes task history, and renders sensitive-action safeguards', async () => {
    await signedIn(); const task={task_id:'task-2',goal:'Send the report',state:'awaiting_approval',observations:[{state:'approval_required',action:'agent.tool.filesystem.write',resource_id:'task-2:0'}]};
    vi.spyOn(globalThis,'fetch').mockResolvedValueOnce(json({tasks:[]})).mockResolvedValueOnce(json(task,202)).mockResolvedValueOnce(json({tasks:[task]})).mockResolvedValueOnce(json(task));
    fireEvent.click(screen.getByRole('button',{name:'Agent tasks'})); expect(await screen.findByText('No tasks yet')).toBeInTheDocument(); fireEvent.change(screen.getByLabelText('Agent task goal'),{target:{value:'Send the report'}}); fireEvent.click(screen.getByRole('button',{name:'Submit goal'}));
    expect(await screen.findByText('Review required')).toBeInTheDocument(); expect(screen.getByText('agent.tool.filesystem.write')).toBeInTheDocument(); expect(screen.getByText(/separate authorized reviewer/i)).toBeInTheDocument(); expect(screen.queryByRole('button',{name:'Review and approve'})).not.toBeInTheDocument();
  });
  it('updates profile through the authenticated profile API', async () => {
    await signedIn(); vi.spyOn(globalThis,'fetch').mockResolvedValueOnce(json({...account,display_name:'Alex Updated'})); fireEvent.click(screen.getByRole('button',{name:/profile settings/i})); fireEvent.change(screen.getByLabelText('Display name'),{target:{value:'Alex Updated'}}); fireEvent.click(screen.getByRole('button',{name:'Save changes'})); expect(await screen.findByRole('status')).toHaveTextContent('profile has been updated');
  });
  it('loads administrator users from the existing admin API', async () => {
    await signedIn('admin'); vi.spyOn(globalThis,'fetch').mockResolvedValueOnce(json({users:[{...account,roles:['admin']}]})); fireEvent.click(screen.getByRole('button',{name:'User management'})); expect(await screen.findByText('alex@example.com')).toBeInTheDocument();
  });
  it('shows admin loading and error states and preserves the server access boundary', async () => {
    await signedIn('admin'); const pending=vi.spyOn(globalThis,'fetch').mockImplementationOnce(()=>new Promise(()=>{})); fireEvent.click(screen.getByRole('button',{name:'User management'})); expect(await screen.findByRole('status')).toHaveTextContent('Loading workspace users'); pending.mockRestore();
    cleanup(); localStorage.clear(); await signedIn('user'); const spy=vi.spyOn(globalThis,'fetch').mockResolvedValueOnce(json({error:{message:'Administrator access required'}},403)); fireEvent.click(screen.getByRole('button',{name:'User management'})); expect(await screen.findByText('Administrator access required')).toBeInTheDocument(); expect(spy).toHaveBeenCalledTimes(1);
  });
});
