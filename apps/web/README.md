# Web application

`apps/web` is the repository's React, TypeScript, and Vite frontend. It provides a responsive dark design system with green accents and Inter typography; sign-in and registration; an authenticated dashboard shell; Brain chat; Personal Agent tasks; profile settings; and administrator-only user listing. Shared API requests consume the existing FastAPI `/api/v1` REST contracts. The backend remains authoritative for authentication, authorization, and ownership.

## Run locally

```sh
cd apps/web
cp .env.example .env.local
npm install
npm run dev
```

Set `VITE_API_BASE_URL` to the FastAPI origin if it differs from `http://localhost:8000`. Vite appends `/api/v1`. Configure the API's CORS origins for the Vite development origin as needed. The frontend calls existing login, registration, logout, profile, admin users, Brain, and Agent APIs. External AI APIs remain optional and are not called directly by this app.

## Security notes

The browser stores the bearer token in local storage to match the current API contract. This is not an authorization boundary; backend checks must remain authoritative. Administrator navigation is a convenience only, and the server enforces access. Do not store provider credentials or secrets in the web client. The API currently uses process-local authentication/task state; consult `services/api/README.md` for operational limitations.

## Tests and build

```sh
npm test
npm run build
```

UI tests cover authentication errors and registration, dashboard navigation, API-backed chat and Agent workflows, profile updates, and admin user loading/access. Test sources are not evidence of execution; report results only after running the commands.
