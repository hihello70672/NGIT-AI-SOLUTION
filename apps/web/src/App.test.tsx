import { afterEach, describe, expect, it, vi } from 'vitest';
import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import App from './App';

afterEach(() => { cleanup(); localStorage.clear(); vi.restoreAllMocks(); });
const account = { id:'u-1', email:'alex@example.com', display_name:'Alex Morgan', status:'active', roles:['user'], created_at:'2025-01-02T00:00:00Z' };
function response(data: unknown, status=200) { return new Response(JSON.stringify(data), { status, headers:{'Content-Type':'application/json'} }); }
describe('NGIT web application', () => {
  it('renders sign in and displays API errors accessibly', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(response({error:{message:'Email or password is incorrect'}},401)));
    render(<App/>); expect(screen.getByRole('heading',{name:/make room for/i})).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText('Email address'),{target:{value:account.email}}); fireEvent.change(screen.getByLabelText('Password'),{target:{value:'incorrect'}}); fireEvent.click(screen.getByRole('button',{name:'Sign in'}));
    expect(await screen.findByRole('alert')).toHaveTextContent('Email or password is incorrect');
  });
  it('loads dashboard, updates profile through API, and handles logout', async () => {
    localStorage.setItem('ngit_access_token','token');
    const fetchMock=vi.fn().mockResolvedValueOnce(response(account)).mockResolvedValueOnce(response({...account,display_name:'Alex Rivera'})).mockResolvedValueOnce(new Response(null,{status:204}));vi.stubGlobal('fetch',fetchMock);
    render(<App/>); expect(await screen.findByRole('heading',{name:'Good to have you here, Alex.'})).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button',{name:'Profile settings'}));fireEvent.change(screen.getByLabelText('Display name'),{target:{value:'Alex Rivera'}});fireEvent.click(screen.getByRole('button',{name:'Save changes'}));
    expect(await screen.findByRole('status')).toHaveTextContent('Your profile has been updated.'); expect(fetchMock).toHaveBeenCalledWith(expect.stringContaining('/api/v1/users/me'),expect.objectContaining({method:'PATCH'}));
    fireEvent.click(screen.getByRole('button',{name:'Sign out'}));expect(await screen.findByRole('heading',{name:/make room for/i})).toBeInTheDocument();expect(localStorage.getItem('ngit_access_token')).toBeNull();
  });
  it('shows backend-authoritative access denial for regular users', async () => {
    localStorage.setItem('ngit_access_token','token');vi.stubGlobal('fetch',vi.fn().mockResolvedValueOnce(response(account)).mockResolvedValueOnce(response({error:{message:'Permission denied'}},403)));
    render(<App/>);await screen.findByRole('heading',{name:/good to have you here/i});fireEvent.click(screen.getByRole('button',{name:/user management/i}));expect(await screen.findByRole('heading',{name:'Administrator access required'})).toBeInTheDocument();
  });
  it('renders empty state after admin user list loads', async () => {
    localStorage.setItem('ngit_access_token','token');vi.stubGlobal('fetch',vi.fn().mockResolvedValueOnce(response({...account,roles:['admin']})).mockResolvedValueOnce(response([])));
    render(<App/>);await screen.findByRole('heading',{name:/good to have you here/i});fireEvent.click(screen.getByRole('button',{name:/user management/i}));expect(await screen.findByRole('heading',{name:'No users to show'})).toBeInTheDocument();
  });
  it('shows user list loading and recoverable error states', async () => {
    localStorage.setItem('ngit_access_token','token');const fetchMock=vi.fn().mockResolvedValueOnce(response({...account,roles:['admin']})).mockResolvedValueOnce(response({error:{message:'Service unavailable'}},503)).mockResolvedValueOnce(response([]));vi.stubGlobal('fetch',fetchMock);
    render(<App/>);await screen.findByRole('heading',{name:/good to have you here/i});fireEvent.click(screen.getByRole('button',{name:/user management/i}));expect(await screen.findByRole('heading',{name:'We couldn’t load users'})).toBeInTheDocument();fireEvent.click(screen.getByRole('button',{name:'Try again'}));expect(await screen.findByRole('heading',{name:'No users to show'})).toBeInTheDocument();
  });
  it('clears an expired session and returns to sign in', async () => {
    localStorage.setItem('ngit_access_token','expired');vi.stubGlobal('fetch',vi.fn().mockResolvedValue(response({error:{message:'Authentication required'}},401)));
    render(<App/>);expect(await screen.findByRole('heading',{name:/make room for/i})).toBeInTheDocument();expect(localStorage.getItem('ngit_access_token')).toBeNull();
  });
});

