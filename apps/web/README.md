# Web application

`apps/web` is the planned frontend application, built with the repository's existing React, TypeScript, and Vite toolchain. The UI provides a responsive dark design system with green accents and Inter typography, sign-in/registration, a user dashboard shell, profile settings, and API-backed administrator user management. Loading, empty, error, retry, and authorization states are explicit.

## Run locally

```sh
cd apps/web
cp .env.example .env.local
npm install
npm run dev
```

Configure `VITE_API_BASE_URL` in `.env.local` for the FastAPI origin (default `http://localhost:8000`). API routes use `/api/v1/auth/login`, `/auth/register`, `/auth/logout`, `/users/me`, and `/admin/users`. Start and configure the API as described in `../../services/api/README.md`.

## Checks

```sh
npm test
npm run build
```

The UI tests exercise sign-in error handling, profile updates and logout, backend authorization denial, and user-list loading, empty, error, retry, and expired-session behavior. The browser stores the bearer token in local storage to support the current API contract; this does not provide an authorization boundary. API authorization remains authoritative for resource ownership and administrator access. Administrator listing is read-only. External AI provider credentials are neither needed nor included.

Test and build commands have not been run as part of the Phase 3 implementation; results remain unverified.
