# NGIT API service

FastAPI identity, security, and modular capability APIs. From the repository root:

```sh
python -m venv .venv
. .venv/bin/activate
pip install -r services/api/requirements.txt
cp .env.example .env
```

Configure unique local `AUTH_TOKEN_PEPPER` (32+ bytes) and `PASSWORD_PEPPER` (16+ bytes), plus `DATABASE_URL` or `POSTGRES_*`, for a migrated PostgreSQL database. Start with `PYTHONPATH=. uvicorn services.api.app:app --reload`. The API never applies privileged migrations; use a non-owner, non-superuser application role without `BYPASSRLS`. Authenticated DB operations set `ngit.user_id` transaction-locally from verified server identity.

## API and operational contracts

OpenAPI is available at `/docs` and `/openapi.json`; default prefix is `/api/v1`. `POST /auth/register` and `POST /auth/login` return bearer tokens and public user data; `POST /auth/logout` revokes the caller's token. `GET/PATCH /users/me` is owner-scoped, and `GET /users` is admin-only with bounded pagination. Brain and memory routers are included; agent routes are enabled only when a workspace is explicitly configured. Health liveness is `GET /health`. Errors use `{ "error": { "code", "message", "request_id", "details" } }`; request IDs are returned in `X-Request-ID`.

No WebSocket is mounted: the approved shared interface does not require bidirectional transport. The process-local background task registry reports task state but does not promise durable delivery, retries, cancellation, or persistent results. External AI APIs remain optional.

Run API tests from the repository root: `PYTHONPATH=. python -m pytest services/api/tests`. PostgreSQL integration tests require the separate disposable database setup in `services/api/db/tests/README.md`. Test source is not evidence that tests ran; record actual execution separately.

## Limitations

Tokens, approvals, emergency-stop, audit, billing, and task state are process-local and lost on restart. Use a single API worker until approved shared persistence is implemented and verified. Environment secret lookup is a configuration primitive, not production secret management. Browser local storage is not an authorization boundary. Never commit real credentials.
