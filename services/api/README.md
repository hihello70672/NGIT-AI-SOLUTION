# NGIT API

FastAPI identity API and modular service routes. Copy root `.env.example` to a private local `.env`, replace example peppers with generated random values, and inject them before starting the API. Database credentials are for local use only. The application uses the configured PostgreSQL schema and transaction-local authenticated-user context; provision a constrained PostgreSQL application role for RLS-protected paths.

## Run locally

From repository root:

```sh
python -m pip install -r services/api/requirements.txt
# Start PostgreSQL and apply migrations as documented in db/README.md.
PYTHONPATH=. uvicorn services.api.app:app --reload
```

Migrations are intentionally not run automatically during API startup. `/health` is process liveness, not database readiness.

## REST API

OpenAPI JSON is served at `/openapi.json` and Swagger UI at `/docs`. The prefix defaults to `/api/v1`.

- `POST /api/v1/auth/register`: validated registration and bearer-token response.
- `POST /api/v1/auth/login`: authenticate email/password; token remains opaque and process-local.
- `POST /api/v1/auth/logout`: revoke the presented bearer token.
- `GET /api/v1/users/me`, `PATCH /api/v1/users/me`: authenticated profile access; only `display_name` is writable.
- `GET /api/v1/users`: admin-only, bounded pagination.
- Brain, memory, and configured agent routes are mounted from their modules and require authenticated callers.

Errors use a stable `error` object with code, safe message, request ID and details. Validation is 422, authentication 401, authorization 403, uniqueness conflict 409, and unexpected failures return a generic 500. Do not expose credentials, token material or stack traces in responses.

Passwords are hashed with scrypt and a server-side pepper. Tokens and approval/emergency-stop state are process-local; run one worker until approved shared durable state is implemented. The admin user listing intentionally denies default users. No WebSocket endpoint is exposed: current contracts are request/response and the shared streaming-delivery guarantees are undecided. Task interfaces do not imply durable background execution. External AI endpoints remain optional.

## Tests

From repository root, with dependencies installed:

```sh
PYTHONPATH=. python -m pytest services/api/tests
```

Tests use fakes where appropriate and do not validate PostgreSQL, migrations, RLS, multi-worker state or deployment readiness. A command must be executed before describing its result as passing. See `docs/STATUS.md` for validation gaps.
