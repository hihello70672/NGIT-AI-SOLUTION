# API and security tests

Run from repository root:

```sh
PYTHONPATH=. python -m pytest services/api/tests
```

Tests use isolated disposable values. HTTP API tests set `AUTH_TOKEN_PEPPER` and `PASSWORD_PEPPER` to non-production values before importing the application and replace user persistence with an in-memory fake where appropriate. Security unit tests exercise token lifecycle, policy and owner checks, exact-scope approvals, atomic single use, emergency stop and audit redaction.

Agent coverage exercises deterministic planning, tool registry allowlisting, workspace sandbox and verification, approval pauses for sensitive writes, exact action/resource binding, task ownership/history, rejection without side effects, browser URL validation, computer adapter boundary and authenticated API routes. Browser and computer adapters in tests are injected fakes; tests do not access external websites or control a desktop.

The suite does not validate PostgreSQL, migrations, RLS, connection pooling, multi-worker state or deployment readiness. Run SQL schema/RLS checks separately against a disposable database using `services/api/db/tests/README.md`. The checked-in suite has not been executed for this implementation update; source tests alone do not establish passing behavior.

Production must inject unique `AUTH_TOKEN_PEPPER` (at least 32 bytes) and `PASSWORD_PEPPER` (at least 16 bytes) through a secret mechanism. Never use test values or commit credentials. Tokens, approval grants, emergency-stop state, audit and agent task history remain process-local; deploy one worker until shared durable state and lifecycle are designed and validated.

## Agent API

When `NGIT_AGENT_WORKSPACE` is configured, authenticated routes mount under `/api/v1/agent`: list tools, submit a task, read owner-scoped task history, request a grant for the exact pending action/resource, resume with the grant, or reject. A grant request does not approve the action. A distinct authenticated reviewer decides through `POST /api/v1/agent/approvals/{approval_id}/decision`; the shared engine enforces separation of duties. Browser navigation/computer actions require explicitly configured adapters. Filesystem access is bounded to the configured workspace. Execution is synchronous, not a durable background queue.

Record exact outcomes only after running tests.
