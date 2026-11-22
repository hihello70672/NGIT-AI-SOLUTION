# Web application

`apps/web` is the sole planned frontend. It uses React, TypeScript and Vite, with Vitest and Testing Library for UI tests. The interface follows the approved dark design, green accents, Inter typography, responsive layouts, and explicit loading/error/empty states.

## Run locally

```sh
cd apps/web
cp .env.example .env.local
npm install
npm run dev
```

Set `VITE_API_BASE_URL` in `.env.local` to the FastAPI origin (default `http://localhost:8000`). The client calls the implemented `/api/v1/auth/login`, `/auth/register`, `/auth/logout`, `/users/me`, and `/admin/users` endpoints. Start/configure the API as described in `../../services/api/README.md`.

```sh
npm test
npm run build
```

The browser stores the bearer token in local storage to support the current API contract. This is a client integration choice, not an authorization boundary: the API remains authoritative for user isolation and administrator permissions. Profile edits and administrator user listing are API-backed; account creation is available from the sign-in screen. Admin listing is read-only. External AI providers are not required.
