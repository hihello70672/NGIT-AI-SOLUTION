# NGIT API service

FastAPI identity, security, user and modular capability APIs. Install from the repository root:

```sh
python -m venv .venv
. .venv/bin/activate
pip install -r services/api/requirements.txt
cp .env.example .env
```

Configure unique local `AUTH_TOKEN_PEPPER` (32+ bytes) and `PASSWORD_PEPPER` (16+ bytes), plus `DATABASE_URL` or `POSTGRES_*` for a migrated PostgreSQL database. Start from the root with `PYTHONPATH=. uvicorn services.api.app:app --reload`. The API never applies privileged migrations; use a non-owner/non-superuser application role without `BYPASSRLS`. Authenticated DB operations set `ngit.user_id` transaction-locally from authenticated server context.

## REST and OpenAPI

OpenAPI is available at `/docs` and `/openapi.json`. The default prefix is `/api/v1`:

- `POST /auth/register` and `POST /auth/login` issue bearer tokens with public user data.
- `POST /auth/logout` revokes the bearer token.
- `GET /users/me` and `PATCH /users/me` access the authenticated profile.
- `GET /users?limit=100&offset=0` is admin-only and paginated.
- Brain and memory routes mount under the same prefix. Agent routes mount only when `NGIT_AGENT_WORKSPACE` is configured.
- `GET /health` is a liveness endpoint.

Memory includes owner-scoped conversation/message, memory search, and allowlisted verified knowledge-ingestion REST APIs. No WebSocket is mounted: the approved shared interfaces require no bidirectional endpoint. External AI is optional.

Errors use `{ "error": { "code", "message", "request_id", "details" } }`; request IDs are returned as `X-Request-ID`.

`services/api/services/tasks.py` provides a process-local background-task interface with accepted/succeeded/failed status and safe failure messages. It does not claim durable queuing, cross-worker delivery, retries, cancellation, or persisted task results; select a durable runner only through architecture review.

Run API tests from root with `PYTHONPATH=. python -m pytest services/api/tests`. Database checks require a disposable migrated PostgreSQL database and non-owner role; see `db/tests/README.md`.

## Limits

Tokens, approvals, emergency-stop and audit state are process-local and lost on restart. Operate one API worker until durable shared state is approved and implemented. Environment secret lookup is for development, not production secret management. Browser local storage is not an authorization boundary. Never commit real credentials.
