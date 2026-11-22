# Web application

`apps/web` is the repository's React, TypeScript, and Vite frontend. It provides a responsive dark design system with green accents and Inter typography, sign-in and registration, an authenticated dashboard shell, overview, Brain chat, Personal Agent tasks, profile settings, and a read-only administrator user listing. Shared API requests use the existing FastAPI `/api/v1` REST contracts; the backend remains responsible for authentication, authorization, and ownership.

## Run locally

```sh
cd apps/web
cp .env.example .env.local
npm install
npm run dev
```

Set `VITE_API_BASE_URL` to the FastAPI origin (defaults to `http://localhost:8000`). Vite appends `/api/v1`; routes consumed include `POST /auth/login`, `POST /auth/register`, `POST /auth/logout`, `GET /users/me`, `PATCH /users/me`, and admin-only `GET /users?limit=100&offset=0`. Brain and Agent routes are documented in `services/api/README.md`. Configure the API's CORS origins for the Vite development origin as needed.

The browser stores the bearer token in local storage to match the current API contract. This is not an authorization boundary; backend checks must remain in place. Administrator navigation is a convenience only: the server enforces access. Do not store provider credentials or secrets in the web client. External AI APIs are optional and are not called directly by this app.

## Tests and build

```sh
npm test
npm run build
```

UI tests cover authentication errors and registration, dashboard navigation, API-backed chat and Agent flows, profile settings, and administrator user listing/access. Test sources are not evidence of execution; record results only after actually running the commands.
