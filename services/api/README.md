# NGIT API

FastAPI identity API and modular services. Configuration is environment-backed; copy the root `.env.example`, set a unique `AUTH_TOKEN_PEPPER` of at least 32 bytes and a stable `PASSWORD_PEPPER` before starting. The sample database credentials are local-only. Use a constrained PostgreSQL application role for RLS.

## Run locally

From the repository root, install the API requirements and start the server:

```sh
python -m pip install -r services/api/requirements.txt
PYTHONPATH=. uvicorn services.api.app:app --reload
```

Apply SQL migrations separately as documented in `db/README.md`. The API expects the database schema and reference seeds to be applied before use. `/health` is a basic process health check and does not prove database readiness.

## API

FastAPI publishes OpenAPI at `/openapi.json` and interactive Swagger UI at `/docs`. REST endpoints are versioned under `/api/v1`. Register and login return an opaque bearer token; send it as `Authorization: Bearer <token>`. `POST /api/v1/auth/logout` revokes the current process-local token. User profile routes derive identity only from validated bearer credentials. Validation, authentication, authorization, conflicts, and unexpected errors use the shared error envelope and request ID. Admin policy controls remain server-side.

The token registry and shared security audit/approval state are process-local; use one worker for this development implementation. Do not present these as durable or cross-worker production sessions. No WebSocket is introduced: existing APIs are request/response and shared protocol requires justification before streaming. Background task contract is synchronous/process-local in `services/tasks.py`; runner/durability remains undecided.

## Tests

Run from repository root:

```sh
PYTHONPATH=. python -m pytest services/api/tests
```

The HTTP API tests isolate the user persistence boundary. Run PostgreSQL migrations and RLS checks separately using `services/api/db/tests/run.sh` against a disposable database. No test is claimed as passed unless actually executed.
