# NGIT API service

FastAPI identity, security, user and modular capability API. Install dependencies with `pip install -r services/api/requirements.txt` and run from the repository root with `PYTHONPATH=. uvicorn services.api.app:app --reload`.

## Security configuration and operational boundary

Copy `.env.example` to a private local environment file and use unique random values for `AUTH_TOKEN_PEPPER` (at least 32 bytes) and `PASSWORD_PEPPER` (at least 16 bytes). Never commit real credentials. Auth and password services read these environment variables; the environment is a local lookup mechanism, not production secret management. Deployments should inject secrets through an approved secret manager.

Authentication tokens, approvals, emergency-stop state and audit state currently live in process memory. Run exactly one API worker and expect state to be lost on restart. Do not claim multi-worker enforcement, durable audit, cross-worker revocation or production readiness until shared persistence and corresponding integration tests exist.

Policy authorization is deny-by-default, role and owner scoped. Restricted operations require exact-resource short-lived approval from a different authenticated reviewer and are blocked while emergency stop is engaged. Agent decisions require `admin` permission through `agent.approval.decide`; both route and approval engine enforce reviewer policy and separation. Missing policy dependencies fail closed. Endpoint tests do not replace service-boundary authorization or database RLS.

## Tests

Run API tests from repository root with `PYTHONPATH=. python -m pytest services/api/tests`. Database tests require a disposable PostgreSQL instance; see `services/api/db/tests/README.md`. A documented command is not evidence it has run.
