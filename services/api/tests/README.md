# API and security tests

Run from the repository root:

```sh
PYTHONPATH=. python -m pytest services/api/tests
```

Use isolated test values. The HTTP API tests set `AUTH_TOKEN_PEPPER` and `PASSWORD_PEPPER` to disposable values before importing the application and replace user persistence with an in-memory fake. They exercise registration/login, token revocation, profile ownership, request correlation, validation, conflict handling and protected Brain routing. Security unit tests exercise token lifecycle, policy and owner checks, exact-scope approvals, atomic single use, emergency stop and audit redaction.

The suite does not validate PostgreSQL, migrations, RLS, connection pooling, multiple worker state or deployment readiness. Run SQL schema/RLS checks separately against a disposable database using the instructions under `services/api/db/tests/README.md`. Tests here have not been executed as part of the documented implementation update.

Production must inject unique `AUTH_TOKEN_PEPPER` (at least 32 bytes) and `PASSWORD_PEPPER` (at least 16 bytes) values through a secret mechanism. Never use test values or commit credentials. Tokens, approval grants, emergency-stop state and audit records currently remain process-local; deploy a single worker until shared state is designed and verified.
