# NGIT API

FastAPI identity API and modular services. Configuration is environment-backed; copy the root `.env.example`, then set unique `AUTH_TOKEN_PEPPER` (at least 32 bytes) and `PASSWORD_PEPPER` (at least 16 bytes) through deployment secret injection before starting. Sample database credentials are local-only. Use a constrained PostgreSQL application role for RLS.

## Run locally

From the repository root:

```sh
python -m pip install -r services/api/requirements.txt
PYTHONPATH=. uvicorn services.api.app:app --reload
```

Apply SQL migrations separately as documented in `db/README.md`. The API expects the schema and reference seeds to exist. `/health` is a process liveness check, not a database-readiness check.

## REST API and OpenAPI

OpenAPI JSON is available at `/openapi.json`; Swagger UI is at `/docs`. Versioned routes use `/api/v1`:

- `POST /auth/register` and `POST /auth/login` accept validated credentials and return an opaque bearer token and public user profile.
- `POST /auth/logout` revokes the presented token.
- `GET /users/me` and `PATCH /users/me` use identity derived from the bearer token; profile updates only permit `display_name`.
- Existing Brain routes are protected by a router-level authentication dependency. Memory and optional agent routes retain module contracts.

Send `Authorization: Bearer <token>`. Tokens expire and are revocable. Passwords use scrypt with an environment-backed pepper. Admin authorization remains server-side. Safe errors carry a stable code and request ID; request validation returns 422 and database uniqueness conflicts return 409.

Tokens, approval and audit stores are process-local. Run a single worker only; these stores are not durable or cross-worker safe. No WebSocket is exposed: current routes are request/response, and shared streaming authentication/delivery guarantees are undecided. Background task interface is synchronous and in-process; see `services/api/services/tasks.py`. External AI endpoints remain optional.

## Tests

Run from repository root:

```sh
PYTHONPATH=. python -m pytest services/api/tests
```

HTTP tests substitute the user persistence boundary; database migrations/RLS require disposable PostgreSQL and the documented database test script. No test result is implied unless executed. Security tokens, emergency-stop state, approvals, and audit events are currently in-process only; do not treat as durable or multi-worker safe.
