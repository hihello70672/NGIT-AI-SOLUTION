# Project status — Phases 1–2

Status is based on files present in the reviewed `main` tree at commit `3b4ea82a2a2d53a8318a1672003661fd4a2293da`. The tree confirms the files described below are committed. Tests and runtime checks have not been run for this status update; checked-in test sources do not establish execution or passing outcomes.

## Phase 1 — Foundation, architecture, database and local environment

**Built and committed:** Repository layout and architecture documentation; PostgreSQL 16 local Compose service and environment example; five ordered migrations (`0001–0005`) defining the isolated `ngit` schema and domain tables, reference seeds, indexes, forced row-level security, and tenant-safe video-source constraints. SQL test assertions, a runner, and setup guidance are present. Architecture, dependency map, phase plan, agent assignments, ERD, shared protocols and module interface docs are committed.

**Remaining:** Apply migrations to a fresh PostgreSQL instance; verify grants and tenant isolation with an application role that is neither table owner nor superuser and lacks `BYPASSRLS`; confirm migration lifecycle and Compose startup. Run the SQL assertions and record the environment and outcome.

**Blockers and caveats:** Database and Compose behavior have not been verified. Migration execution is privileged; RLS validation must use the separate non-owner/non-superuser application role. The API must set `ngit.user_id` transaction-locally from authenticated server context. Provider metadata is for opaque credential references, not secrets. External AI is optional.

## Phase 2 — Authentication, security, API, users and web client

**Built and committed:** FastAPI application/configuration, request IDs, safe errors, user and authentication services, REST endpoints/schemas, PostgreSQL caller context, and backend authorization. Security primitives include expiring/revocable opaque bearer tokens, allow-list role and owner policy checks, exact-scope approvals with expiry, reviewer separation and atomic consumption, restricted-action authorization, emergency stop, redacted audit events and environment-backed secret lookup. Agent approval decisions enforce administrator policy and task-owner separation. React/TypeScript/Vite web client provides sign-in/registration, authenticated dashboard, profile settings and read-only administrator listing, with responsive/accessibility states and shared API client. Backend, database integration, security, agent API and web UI test sources are committed.

**Remaining:** Run backend and frontend test suites, build the production frontend, execute opt-in PostgreSQL-backed API integration and SQL/RLS assertions, and verify end-to-end local startup. Review authorization boundaries and database role behavior; record exact commands and results only after running them.

**Blockers and caveats:** No tests or runtime checks have been run for this update, including Python/API, frontend tests/build, migrations/RLS, Compose, or live integration. PostgreSQL integration requires a disposable migrated database and a suitable non-owner/non-superuser role. Auth tokens, approvals, emergency-stop state and audit events are process-local: use one API worker until shared durable state exists. Environment lookup is not production secret management; browser local-storage bearer tokens are not an authorization boundary.

## Validation record

Tests and runtime checks have not been run for this update. In particular, no passing result is claimed for Python/API or web tests, frontend build, PostgreSQL migration/RLS checks, Compose startup, or end-to-end integration.

## Next work

1. Run the documented backend and frontend suites and address failures.
2. Run migrations and SQL/RLS assertions against disposable PostgreSQL using the required non-owner/non-superuser application role; verify grants and transaction-local caller context.
3. Verify Compose and local API/web startup and PostgreSQL-backed identity integration.
4. Review security boundaries and plan durable shared state before enabling multiple API workers.
5. Update this record with exact commands and observed outcomes after validation.

Documented backend command (not reported as run):

```bash
PYTHONPATH=. python -m pytest services/api/tests
```

Database setup and test instructions are in `services/api/db/tests/README.md` and `services/api/tests/README.md`.
