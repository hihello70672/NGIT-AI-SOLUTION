# NGIT API service

FastAPI identity, security, user and modular capability API. Install dependencies with `pip install -r services/api/requirements.txt` and run locally from the repository root with `PYTHONPATH=. uvicorn services.api.app:app --reload`.

## Security configuration and operational boundary

Copy `.env.example` to a private local environment file and provide unique random values for `AUTH_TOKEN_PEPPER` (at least 32 bytes) and `PASSWORD_PEPPER` (at least 16 bytes). Never commit real credentials. `SecretStore` validates environment variable names and provides lookup only; it is not a production secret-management backend. Deployments should inject secrets through an approved secret manager.

Authentication tokens, approvals, emergency-stop state and audit state currently live in process memory. Run exactly one API worker and expect state to be lost on restart. Do not claim multi-worker enforcement, durable audit, revocation across workers, or production readiness until shared persistence and corresponding integration tests are implemented.

Policy authorization is deny-by-default, role and owner scoped. Restricted operations require an exact-resource, short-lived approval from a different authenticated reviewer, and are blocked while emergency stop is engaged. Agent approval decisions require the `admin` role through `agent.approval.decide`; the policy is checked by the API route and approval engine, and task owners cannot decide their own requests. All missing reviewer-policy dependencies fail closed. Endpoint checks and unit tests do not replace service-boundary authorization or database RLS.

## Tests

Run API tests from the repository root with `PYTHONPATH=. python -m pytest services/api/tests`. Database migration/RLS tests need a disposable PostgreSQL instance; see `services/api/db/tests/README.md`. A documented command is not evidence that it has run.
