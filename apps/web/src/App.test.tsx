import { afterEach, describe, expect, it, vi } from 'vitest';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import App from './App';

afterEach(() => { cleanup(); localStorage.clear(); vi.restoreAllMocks(); });
const account = { id:'u-1', email:'alex@example.com', display_name:'Alex Morgan', status:'active', roles:['user'], created_at:'2025-01-02T00:00:00Z' };
function json(data: unknown, status=200) { return new Response(JSON.stringify(data), { status, headers:{'Content-Type':'application/json'} }); }
describe('NGIT web application', () => {
 it('renders a responsive sign-in surface and reports API errors accessibly', async () => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue(json({error:{message:'Email or password is incorrect'}} ,401)));
  render(<App/>); expect(screen.getByRole('heading',{name:'Make room for what matters.'})).toBeInTheDocument();
  fireEvent.change(screen.getByLabelText('Email address'),{target:{value:'alex@example.com'}}); fireEvent.change(screen.getByLabelText('Password'),{target:{value:'wrong'}}); fireEvent.click(screen.getByRole('button',{name:'Sign in'}));
  expect(await screen.findByRole('alert')).toHaveTextContent('Email or password is incorrect');
 });
 it('loads the signed-in dashboard and updates profile through the API', async () => {
  localStorage.setItem('ngit_access_token','token');
  vi.stubGlobal('fetch',vi.fn().mockResolvedValueOnce(json(account)).mockResolvedValueOnce(json({...account,display_name:'Alex Rivera'})));
  render(<App/>); expect(await screen.findByRole('heading',{name:'Good to have you here, Alex.'})).toBeInTheDocument();
  fireEvent.click(screen.getByRole('button',{name:'Profile settings'})); expect(await screen.findByRole('heading',{name:'Profile settings'})).toBeInTheDocument();
  fireEvent.change(screen.getByLabelText('Display name'),{target:{value:'Alex Rivera'}}); fireEvent.click(screen.getByRole('button',{name:'Save changes'}));
  expect(await screen.findByRole('status')).toHaveTextContent('Your profile has been updated.');
  expect(fetch).toHaveBeenLastCalledWith(expect.stringContaining('/api/v1/users/me'),expect.objectContaining({method:'PATCH',headers:expect.any(Headers),body:JSON.stringify({display_name:'Alex Rivera'})}));
 });
 it('shows backend authorization denial on user management and supports retry state', async () => {
  localStorage.setItem('ngit_access_token','token');
  vi.stubGlobal('fetch',vi.fn().mockResolvedValueOnce(json(account)).mockResolvedValueOnce(json({error:{message:'Permission denied'}},403)));
  render(<App/>); await screen.findByRole('heading',{name:'Good to have you here, Alex.'}); fireEvent.click(screen.getByRole('button',{name:/User management/}));
  expect(await screen.findByRole('heading',{name:'Administrator access required'})).toBeInTheDocument();
 });
});
