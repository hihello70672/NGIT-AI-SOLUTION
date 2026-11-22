# NGIT API

FastAPI identity API and modular services. Configuration is environment-backed; copy the root `.env.example`, set a unique `AUTH_TOKEN_PEPPER` of at least 32 bytes and a stable `PASSWORD_PEPPER` before starting. Sample database credentials are local-only. Use a constrained PostgreSQL application role for RLS.

## Run locally

From the repository root, install dependencies and start the server:

```sh
python -m pip install -r services/api/requirements.txt
PYTHONPATH=. uvicorn services.api.app:app --reload
```

Apply SQL migrations separately as documented in `db/README.md`. The API expects its schema and reference seeds to exist. `/health` is a process liveness check, not database readiness.

## REST API

OpenAPI JSON is available at `/openapi.json`; Swagger UI at `/docs`. Versioned REST endpoints use `/api/v1`:

- `POST /auth/register` and `POST /auth/login` accept validated credentials and return an opaque bearer token and public user profile.
- `POST /auth/logout` revokes the presented token.
- `GET /users/me` and `PATCH /users/me` only access the identity derived from the validated bearer token.
- Existing Brain endpoints are protected by a router-level auth guard. Memory and optional agent routes retain module contracts.

Send `Authorization: Bearer <token>`. Tokens expire and are revocable. Passwords use scrypt with an environment-backed pepper. Admin authorization remains server-side. Security errors, validation failures, conflicts and unexpected errors use safe response envelopes; responses carry `X-Request-ID`.

Token, approval and audit stores are process-local in this implementation. Run a single worker only; do not represent state as durable or cross-worker safe. A shared persistence adapter and durable task runner need approved design before production use. No WebSocket is exposed: current endpoints are request/response, and shared streaming authentication/delivery guarantees have not been decided. Background task interface is synchronous and in-process; see `services/api/services/tasks.py`. External AI endpoints remain optional.

## Tests

Run from repository root:

```sh
PYTHONPATH=. python -m pytest services/api/tests
```

HTTP tests substitute the user persistence boundary; database migrations/RLS require a disposable PostgreSQL instance and the documented database test script. No test result is implied unless executed.
