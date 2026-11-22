# Project status — Phases 1–2

Status is based on the files present in the reviewed default-branch tree at the time of this update. The tree confirms the implementation and documentation described below are committed. Tests and runtime checks have not been run for this status update; checked-in test sources do not establish execution or passing outcomes.

## Phase 1 — Foundation, architecture, database and local environment

**Built and committed:** Repository layout for the web client, FastAPI service, database, documentation and Docker guidance; architecture, dependency map, phase plan, agent assignments, ERD, shared protocols and module interface documents; PostgreSQL 16 Compose service and environment templates; five ordered database migration files (`0001`–`0005`) defining the `ngit` schema, reference seeds, domain tables, indexes, forced row-level security (RLS), tenant constraints and tenant-safe video source relationship. SQL assertions, a runner and database setup guidance are present.

**Remaining:** Apply migrations to a fresh PostgreSQL instance; verify migration lifecycle, grants and RLS/tenant isolation using the required non-owner, non-superuser application role without `BYPASSRLS`; validate Compose startup and environment configuration.

**Blockers/caveats:** Database and Compose behavior has not been verified. Migration execution requires a privileged migration role; RLS checks require a distinct application role and transaction-local `ngit.user_id` derived from authenticated server context. Provider metadata is not a place for secrets; external AI is optional.

## Phase 2 — Authentication, security, API, users and web client

**Built and committed:** FastAPI app/configuration, identity and user services, REST schemas and endpoints, request IDs and safe error handling; PostgreSQL caller context; process-local bearer-token authentication/revocation, role/owner policy enforcement, scoped approvals, restricted-action authorization, emergency stop, redacted audit and environment-backed secret lookup. The API composes Brain and memory routes and conditionally enables agent routes when configured. The React/TypeScript/Vite client includes sign-in/registration, authenticated dashboard, profile settings, admin user listing, responsive/accessibility states and a shared typed API client. Backend, security, integration and UI test sources, API and web setup guidance are committed.

**Remaining:** Run backend and frontend test suites; build the production frontend; exercise PostgreSQL-backed identity/integration and SQL/RLS checks; verify authorization boundaries and local end-to-end API/web startup. Record exact commands and outcomes only after execution.

**Blockers/caveats:** No tests, builds, migrations, Compose lifecycle checks or live integration checks have been run for this update. Authentication tokens, approvals, emergency-stop state and audit events are process-local and lost on restart; run one API worker until approved durable shared state is implemented. Environment-based secret lookup is development-only; browser token storage is not an authorization boundary. PostgreSQL-backed checks require a disposable migrated database and correctly provisioned application role.

## Validation record

Tests and runtime checks have not been run for this status update. No passing result is claimed for Python/API tests, web tests/build, PostgreSQL migrations/RLS, Compose startup or end-to-end integration. Test sources are not execution evidence. Do not add `docs/TEST_REPORT.md` until tests have actually run; include exact commands, environment and observed outcomes.

## Next work

1. Provision disposable PostgreSQL and distinct migration/application roles; apply all ordered migrations and execute the documented SQL/RLS assertions.
2. Run documented backend and frontend tests, investigate and fix failures, and build the production frontend.
3. Validate Compose lifecycle and end-to-end local API/web operation against PostgreSQL; review authorization and tenant isolation.
4. Document exact validation evidence. Resolve durable shared security state before multi-worker operation.

Phases 1–2 are implemented in part and documented, but are not validated or complete.