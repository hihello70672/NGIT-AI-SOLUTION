# API and security tests

Run from the repository root with `PYTHONPATH=. python -m pytest services/api/tests`.

The HTTP API tests replace the user repository with an in-memory fake and use disposable test pepper values set before importing the application. They exercise registration/login, token revocation, profile ownership, input validation, request correlation, and protected Brain routing. Security unit tests cover digest-only token storage, expiration and revocation, default-deny policies, roles and resource ownership, bound single-use approvals and distinct reviewers, emergency-stop denial/audit, sensitive audit-data redaction, safe errors, and secret-name validation.

These tests do not validate PostgreSQL, migration/RLS behavior, multi-worker persistence, or deployment readiness. Run SQL checks separately with `services/api/db/tests/run.sh` against a disposable PostgreSQL instance. Test pepper values are not production credentials.

Production/deployment configuration must provide `AUTH_TOKEN_PEPPER` (at least 32 bytes) and `PASSWORD_PEPPER` (at least 16 bytes) through a secret injection mechanism. Do not copy real credentials into the repository or `.env.example`.

Security tokens, approval grants, emergency stop state, and audit events are currently in-process only. Do not treat them as durable or multi-worker safe.
