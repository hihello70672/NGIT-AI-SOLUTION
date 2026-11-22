# NGIT API service

FastAPI identity, security, and modular capability APIs. Install from the repository root:

```sh
python -m venv .venv
. .venv/bin/activate
pip install -r services/api/requirements.txt
cp .env.example .env
```

Configure unique local `AUTH_TOKEN_PEPPER` (32+ bytes) and `PASSWORD_PEPPER` (16+ bytes), plus `DATABASE_URL` or `POSTGRES_*`, for a migrated PostgreSQL database. Start from the root with `PYTHONPATH=. uvicorn services.api.app:app --reload`. The API never applies privileged migrations; use a non-owner, non-superuser application role without `BYPASSRLS`. Authenticated DB operations set `ngit.user_id` transaction-locally from server-derived identity.

## REST and OpenAPI

OpenAPI is at `/docs` and `/openapi.json`; the default API prefix is `/api/v1`.

- `POST /auth/register` and `POST /auth/login` issue bearer tokens with public user data.
- `POST /auth/logout` revokes the current token.
- `GET /users/me` and `PATCH /users/me` access/update the authenticated profile.
- `GET /users?limit=100&offset=0` is admin-only and paginated.
- Brain and memory routes are mounted under the same prefix. Agent routes mount only when `NGIT_AGENT_WORKSPACE` is configured.
- `GET /health` is a liveness endpoint.

No WebSocket is mounted: the approved shared interfaces require no bidirectional endpoint. Errors use `{ "error": { "code", "message", "request_id", "details" } }`; request IDs are returned in `X-Request-ID`. The process-local background task registry in `services/api/services/tasks.py` reports accepted/succeeded/failed status but does not promise durable delivery, retries, cancellation, or persisted results. External AI APIs are optional.

Run API tests from root with `PYTHONPATH=. python -m pytest services/api/tests`. Database integration tests require the dedicated disposable test database described in `services/api/tests/README.md`.

## Operational limitations

Tokens, approvals, emergency-stop, audit and task state remain process-local and are lost at restart. Run one API worker until approved shared persistence is implemented and verified. Environment secret lookup is a configuration primitive, not production secret management. Browser local storage is not an authorization boundary. Never commit real credentials.
