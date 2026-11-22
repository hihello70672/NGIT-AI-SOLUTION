# API service

NGIT's modular FastAPI backend exposes versioned REST endpoints at `/api/v1`. Route handlers remain thin; user/auth persistence is in services, PostgreSQL access is mediated by `database.py`, and shared bearer authentication/RBAC/audit primitives are implemented in `security.py`.

## Local startup

1. Copy `.env.example` to `.env`, set `AUTH_TOKEN_PEPPER` to a unique random value of at least 32 bytes, and optionally set `DATABASE_URL` (or the `POSTGRES_*` variables). The password has a separately optional `PASSWORD_PEPPER` setting; configure it consistently before creating accounts and never change it without a migration strategy.
2. Start PostgreSQL from the repository root with `docker compose up -d postgres`.
3. Apply `services/api/db/migrations/0001_initial_schema.sql` and `0002_seed_reference_data.sql` using the documented database test runner or `psql`.
4. Install `services/api/requirements.txt` and start with `PYTHONPATH=. uvicorn services.api.app:app --reload` from the repository root.
5. Browse `/docs` for generated OpenAPI documentation. `/health` is a liveness endpoint; it does not claim database readiness.

## API

- `POST /api/v1/auth/register` and `/auth/login` return an opaque bearer token and user profile. Passwords are stored using salted scrypt hashes.
- `POST /api/v1/auth/logout` revokes the in-process token.
- `GET`/`PATCH /api/v1/users/me` provide the authenticated profile and display-name update.
- `GET /api/v1/admin/users` and `/admin/audit` require admin role; denials are audited.
- Errors use `{ "error": { "code", "message", "request_id", "details" } }`. Validation is 422, unauthenticated is 401, authorization is 403, uniqueness conflicts are 409, and unexpected failures are safely redacted.

The token store and approval state in the previously agreed security interface are process-local; production multi-worker persistence/revocation requires a shared store decision. No WebSocket is needed for this identity phase. AI providers remain optional and are not called by this service.
