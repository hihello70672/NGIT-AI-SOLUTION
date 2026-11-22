# NGIT API service

FastAPI identity, security, user and modular capability API. Install dependencies with `pip install -r services/api/requirements.txt` and run from the repository root with `PYTHONPATH=. uvicorn services.api.app:app --reload`.

## Database and authentication configuration

Copy `.env.example` to a private local environment file and use unique random values for `AUTH_TOKEN_PEPPER` (at least 32 bytes) and `PASSWORD_PEPPER` (at least 16 bytes). Configure `DATABASE_URL` or the `POSTGRES_*` values for a migrated PostgreSQL database. Never commit real credentials. Auth and password services read these environment variables; environment lookup is a local mechanism, not production secret management. Deployments should inject secrets through an approved secret manager.

Database migrations are privileged and are not applied automatically by the API. Use an application database role that is not a superuser, not a table owner and does not have `BYPASSRLS`. Authenticated user-scoped reads and writes set `ngit.user_id` transaction-locally in the service connection. Verify schema grants and RLS using the separate SQL test guidance before deployment.

## Security and operational boundaries

Authentication tokens, approvals, emergency-stop state and audit events currently live in process memory. Run exactly one API worker and expect state to be lost on restart. Do not claim multi-worker enforcement, durable audit, cross-worker revocation or production readiness until shared persistence and corresponding integration tests exist.

Policy authorization is deny-by-default, role and owner scoped. Restricted operations require exact-resource short-lived approval from a different authenticated reviewer and are blocked while emergency stop is engaged. Agent approval decisions require `admin` permission through `agent.approval.decide`; both route and approval engine enforce reviewer policy and separation. Missing policy dependencies fail closed. Endpoint tests do not replace service-boundary authorization or database RLS.

## API and tests

OpenAPI documentation is available at `/docs` and `/openapi.json` when the service is running. Auth routes are under the configured API prefix (default `/api/v1`): `POST /auth/register`, `POST /auth/login`, and authenticated `POST /auth/logout`. User routes are `GET/PATCH /users/me`; `GET /users` is admin-only and paginated. Brain, memory and optionally configured agent routes are mounted under the same prefix. REST is the default; no WebSocket endpoint is needed by the approved interfaces.

Run API tests from repository root with `PYTHONPATH=. python -m pytest services/api/tests`. Database integration tests require a disposable migrated PostgreSQL database and a non-owner, non-superuser role without `BYPASSRLS`; set `NGIT_TEST_DATABASE_URL` to opt in. Database tests are described in `services/api/db/tests/README.md`. A documented command is not evidence it has run.
