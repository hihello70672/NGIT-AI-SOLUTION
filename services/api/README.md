# NGIT API

FastAPI identity API and modular services. Configuration is environment-backed; copy the root `.env.example`, set a unique `AUTH_TOKEN_PEPPER` of at least 32 bytes and a stable `PASSWORD_PEPPER` before starting. Sample database credentials are local-only. Use a constrained PostgreSQL application role for RLS.

## Run locally

From the repository root, install API requirements and start the server:

```sh
python -m pip install -r services/api/requirements.txt
PYTHONPATH=. uvicorn services.api.app:app --reload
```

Apply SQL migrations separately as documented in `db/README.md`. The API expects its schema and reference seeds to exist. `/health` is a basic process health check and does not prove database readiness.

## API and security

FastAPI publishes OpenAPI at `/openapi.json` and Swagger UI at `/docs`. REST endpoints use `/api/v1`. Register and login return opaque bearer tokens; send `Authorization: Bearer <token>`. Tokens are random, held as keyed digests, expire, and can be revoked. User profile routes derive identity only from validated bearer credentials. Admin policy controls remain server-side.

`services/api/security.py` contains the shared authentication, default-deny RBAC/policy, approval, restricted-action, audit, emergency-stop, and environment secret-store primitives. Sensitive actions require a different approver, a live approval bound to actor/action/resource, and a non-engaged stop switch. Authorization decisions and denials are audited with sensitive-field filtering. These stores are process-local: use a single worker for this implementation; do not present it as durable or cross-worker production sessions. Secret values belong only in environment or an approved vault and never in source control or browser code.

No WebSocket is introduced. Existing APIs are request/response; shared protocol requires justification before streaming. Background task contract is synchronous/process-local in `services/tasks.py`; runner/durability remains undecided. External AI endpoints remain optional.

## Tests

Run from repository root:

```sh
PYTHONPATH=. python -m pytest services/api/tests
```

HTTP API tests isolate user persistence. Run PostgreSQL migrations and RLS checks separately using `services/api/db/tests/run.sh` against a disposable database. No test is claimed as passed unless actually executed.
