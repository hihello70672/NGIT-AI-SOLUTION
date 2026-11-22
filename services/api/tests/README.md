# API and security tests

Run from the repository root with `PYTHONPATH=. python -m pytest services/api/tests`.

The HTTP API tests replace the user repository with an in-memory fake and use disposable test pepper values set before importing the application. They exercise registration/login, token revocation, profile ownership, input validation, request correlation, and protected Brain routing. These tests do not validate PostgreSQL, migration/RLS behavior, multi-worker persistence, or deployment readiness. Run SQL checks separately using `services/api/db/tests/run.sh` against disposable PostgreSQL.

Test environment secrets are explicitly test-only and never production credentials.
