# Web application

`apps/web` is the repository's React, TypeScript, and Vite frontend. It provides a responsive dark design system with green accents and Inter typography, sign-in and registration, an authenticated dashboard shell, profile settings, and administrator user management. API requests use the existing `/api/v1` REST contracts; authorization is always enforced by the backend. The interface exposes loading, empty, error, retry, expired-session, and access-denied states.

## Run locally

```sh
cd apps/web
cp .env.example .env.local
npm install
npm run dev
```

Configure `VITE_API_BASE_URL` in `.env.local` for the FastAPI origin (default `http://localhost:8000`). The API routes consumed here are `/api/v1/auth/login`, `/api/v1/auth/register`, `/api/v1/auth/logout`, `/api/v1/users/me`, and `/api/v1/admin/users`. Start and configure the API as described in `../../services/api/README.md`.

## Checks

```sh
npm test
npm run build
```

UI tests cover sign-in and registration errors, profile updates and logout, backend authorization denial, user-list loading/error/retry/empty/populated states, and expired-session recovery. Checks are not claimed until executed. The browser stores the bearer token in local storage to match the current API contract; this is not an authorization boundary or a substitute for backend ownership checks. Admin user listing is read-only. External AI credentials are not used by the web app.

