# NGIT API

FastAPI identity API and modular service routes. Copy the root `.env.example` into a private local `.env` and replace the non-secret examples. Set `AUTH_TOKEN_PEPPER` to a random value of at least 32 bytes and `PASSWORD_PEPPER` to at least 16 bytes using secret injection before startup. Database sample credentials are for local use only. Use a constrained PostgreSQL application role for RLS-protected paths.

## Run locally

From repository root:

```sh
python -m pip install -r services/api/requirements.txt
PYTHONPATH=. uvicorn services.api.app:app --reload
```

Apply SQL migrations separately as documented in `db/README.md`; the API does not run migrations at startup. `/health` is process liveness, not database readiness.

## REST API and OpenAPI

OpenAPI is served at `/openapi.json`; Swagger UI is at `/docs`. API prefix defaults to `/api/v1`.

- `POST /api/v1/auth/register` and `/auth/login`: validate credentials and return an opaque bearer token with public profile.
- `POST /api/v1/auth/logout`: revoke the presented bearer token.
- `GET /api/v1/users/me` and `PATCH /api/v1/users/me`: authenticated profile access; the only writable field is `display_name`.
- Brain, memory, knowledge and configured agent routes are mounted from their modules. Caller identity is derived from bearer credentials at the server boundary.

Errors are returned in an `error` object with stable `code`, safe `message`, request ID and structured `details`. Request IDs are echoed as `X-Request-ID`. Validation returns 422, unauthenticated requests 401, authorization denials 403, uniqueness conflicts 409 and unexpected failures a generic 500 response.

Passwords are hashed with scrypt and an environment pepper; tokens are opaque and process-local. Tokens, approval grants, emergency-stop state and audit events are not durable or shared between workers: run one worker only. WebSockets are intentionally not exposed because current endpoints are request/response and shared streaming delivery/authentication guarantees are undecided. Task routes are synchronous/process-local interfaces, not durable background execution. External AI endpoints remain optional.

## Tests

From repository root, run `PYTHONPATH=. python -m pytest services/api/tests`. Tests replace user persistence with an in-memory fake where appropriate; this does not validate PostgreSQL, migrations, RLS, multi-worker state, or deployment readiness. No result is implied unless the command is executed.

See `docs/STATUS.md` for implementation and verification boundaries.
