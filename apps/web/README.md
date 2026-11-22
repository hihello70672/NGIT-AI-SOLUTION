# Web application

`apps/web` is the sole planned frontend. This implementation uses React, TypeScript, and Vite, with Vitest and Testing Library for UI tests. It follows the approved dark interface, green brand accents, Inter typography, responsive layouts, and explicit loading/error states.

## Run locally

```sh
cd apps/web
cp .env.example .env.local
npm install
npm run dev
```

The API base defaults to `http://localhost:8000`; set `VITE_API_BASE_URL` in `.env.local` to change it. The client consumes the implemented `/api/v1` login, registration, logout, current-user, profile-update, and admin-user-list routes. Start the API and configure its database as documented in `../../services/api/README.md`.

```sh
npm test
npm run build
```

The access token is held in browser local storage to match the current bearer-token API. This is a client integration choice, not an authorization boundary; the backend remains authoritative. User management is read-only and requires the backend to authorize the signed-in user. No external AI provider is required.
