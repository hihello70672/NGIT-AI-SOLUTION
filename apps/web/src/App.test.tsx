import { afterEach, describe, expect, it, vi } from 'vitest';
import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import App from './App';

afterEach(() => { cleanup(); localStorage.clear(); vi.restoreAllMocks(); });
const account = { id:'u-1', email:'alex@example.com', display_name:'Alex Morgan', status:'active', roles:['user'], created_at:'2025-01-02T00:00:00Z' };
function response(data:unknown,status=200){return new Response(JSON.stringify(data),{status,headers:{'Content-Type':'application/json'}});}
describe('NGIT web application',()=>{
 it('renders sign-in and reports backend errors accessibly',async()=>{
  vi.stubGlobal('fetch',vi.fn().mockResolvedValue(response({error:{message:'Email or password is incorrect'}},401)));
  render(<App/>);expect(screen.getByRole('heading',{name:/Make room for/})).toBeInTheDocument();
  fireEvent.change(screen.getByLabelText('Email address'),{target:{value:account.email}});fireEvent.change(screen.getByLabelText('Password'),{target:{value:'incorrect'}});fireEvent.click(screen.getByRole('button',{name:'Sign in'}));
  expect(await screen.findByRole('alert')).toHaveTextContent('Email or password is incorrect');
 });
 it('loads dashboard and updates the profile through the API',async()=>{
  localStorage.setItem('ngit_access_token','token');vi.stubGlobal('fetch',vi.fn().mockResolvedValueOnce(response(account)).mockResolvedValueOnce(response({...account,display_name:'Alex Rivera'})));
  render(<App/>);expect(await screen.findByRole('heading',{name:'Good to have you here, Alex.'})).toBeInTheDocument();fireEvent.click(screen.getByRole('button',{name:'Profile settings'}));
  fireEvent.change(screen.getByLabelText('Display name'),{target:{value:'Alex Rivera'}});fireEvent.click(screen.getByRole('button',{name:'Save changes'}));
  expect(await screen.findByRole('status')).toHaveTextContent('Your profile has been updated.');expect(fetch).toHaveBeenLastCalledWith(expect.stringContaining('/api/v1/users/me'),expect.objectContaining({method:'PATCH',body:JSON.stringify({display_name:'Alex Rivera'})}));
 });
 it('shows backend-authoritative authorization denial for a regular user',async()=>{
  localStorage.setItem('ngit_access_token','token');vi.stubGlobal('fetch',vi.fn().mockResolvedValueOnce(response(account)).mockResolvedValueOnce(response({error:{message:'Permission denied'}},403)));
  render(<App/>);await screen.findByRole('heading',{name:'Good to have you here, Alex.'});fireEvent.click(screen.getByRole('button',{name:/User management/}));
  expect(await screen.findByRole('heading',{name:'Administrator access required'})).toBeInTheDocument();
 });
 it('renders the empty state for an admin user list',async()=>{
  localStorage.setItem('ngit_access_token','token');vi.stubGlobal('fetch',vi.fn().mockResolvedValueOnce(response({...account,roles:['admin']})).mockResolvedValueOnce(response([])));
  render(<App/>);await screen.findByRole('heading',{name:'Good to have you here, Alex.'});fireEvent.click(screen.getByRole('button',{name:/User management/}));expect(await screen.findByRole('heading',{name:'No users to show'})).toBeInTheDocument();
 });
 it('clears an expired session and returns to sign-in',async()=>{
  localStorage.setItem('ngit_access_token','expired');vi.stubGlobal('fetch',vi.fn().mockResolvedValue(response({error:{message:'Authentication required'}},401)));
  render(<App/>);expect(await screen.findByRole('heading',{name:/Make room for/})).toBeInTheDocument();expect(localStorage.getItem('ngit_access_token')).toBeNull();
 });
});
