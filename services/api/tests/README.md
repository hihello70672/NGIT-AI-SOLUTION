# API and security tests

Run from the repository root:

```sh
PYTHONPATH=. python -m pytest services/api/tests
```

Tests use isolated disposable values. HTTP API tests set `AUTH_TOKEN_PEPPER` and `PASSWORD_PEPPER` to non-production values before importing the application and replace user persistence with an in-memory fake where appropriate. Security unit tests exercise token lifecycle, policy and owner checks, exact-scope approvals, atomic single use, emergency stop and audit redaction.

Agent coverage exercises deterministic planning, tool registry allowlisting, workspace sandbox and verification, approval pauses for sensitive writes, exact action/resource approval binding, task ownership/history, rejection without side effects, browser URL validation, computer adapter boundary and authenticated API routes. Browser and computer adapters in tests are injected fakes; tests do not access external websites or control a desktop.

The suite does not validate PostgreSQL, migrations, RLS, connection pooling, multiple-worker state or deployment readiness. Run SQL schema/RLS checks separately against a disposable database using the instructions under `services/api/db/tests/README.md`. The checked-in test suite has not been executed for the documented implementation update; source tests alone do not establish passing behavior.

Production must inject unique `AUTH_TOKEN_PEPPER` (at least 32 bytes) and `PASSWORD_PEPPER` (at least 16 bytes) through a secret mechanism. Never use test values or commit credentials. Tokens, approval grants, emergency-stop state, audit and agent task history currently remain process-local; deploy one worker until shared durable state is designed and validated.

## Agent API

When `NGIT_AGENT_WORKSPACE` is configured, authenticated routes mount under `/api/v1/agent`: list tools, submit a task, read owner-scoped task history, request a grant for the exact pending action/resource, resume with the grant, or reject the task. A request creates a grant; an independent reviewer must decide it through the shared approval engine before execution can resume. Browser navigation and computer actions remain unavailable unless explicitly configured adapters are injected. The filesystem is restricted to the configured workspace. These synchronous adapters are not durable background jobs.

Run the suite from the repository root with dependencies installed; exact outcomes must be recorded only after execution.
