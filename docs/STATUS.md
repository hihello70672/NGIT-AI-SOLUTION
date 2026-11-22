# Project status — Phases 1–3

This status records repository evidence, not proof of runtime behavior. API/database suites and the web suite have not been run in this task; no passing result is claimed.

## Phase 1 — Foundation, architecture, database, local environment

Foundation documentation, Docker Compose PostgreSQL service, ordered SQL migrations, seed data, schema checks, and ERD are committed. The `ngit` schema includes users and roles, user-scoped conversations, messages, memory, billing, optional provider configuration, media/video and presentation metadata, audit logs, supporting indexes, composite ownership constraints, and row-level security policies for user-owned tables. Migration `0003` hardens role-assignment RLS.

The database migration tooling remains deliberately plain ordered SQL. Apply files in `services/api/db/migrations/` in lexicographic order on fresh PostgreSQL 16+. Database/RLS tests and Compose lifecycle still require execution. Migration presence does not establish that the API uses the schema.

## Phase 2 — Authentication, security, API, user management

The FastAPI service exposes versioned REST endpoints for registration, login, logout, current-user profile read/update, protected Brain endpoints, memory, and optional agent integration. Request validation, request IDs, safe error handling, OpenAPI, password hashing, opaque expiring/revocable bearer tokens, role and ownership policies, approvals, and audit primitives are included. User identity persistence uses PostgreSQL-backed services and the existing connection pool with transaction-local user context for RLS-scoped access. Password and token peppers must be configured in the environment; no real secrets are committed.

Token/approval/audit state remains process-local; only a single worker is supported until an approved shared adapter exists. Background-task support is an in-process interface, not durable execution. Existing endpoints are request/response, so no WebSocket was justified or added. External AI APIs remain optional. API tests and live database integration have not been executed in this task.

## Phase 3 — Web application foundation

`apps/web` contains a responsive React/Vite application with the Inter dark design system and green brand accents, sign-in/registration, authenticated dashboard shell, profile settings, and role-aware user-management view. Existing shared API client is consumed for login, registration, session validation, profile update, logout, and administrator user listing; the UI treats backend authorization as authoritative and includes loading, empty, error, and retry states. UI tests cover sign-in errors, profile updates/logout, authorization denial, empty/loading/error states, and expired sessions. Tests were not run in this task, so their results remain unverified.

## Remaining validation and integration

- Run API/unit and web suites and record exact commands/outcomes.
- Run SQL migrations and RLS tests on disposable PostgreSQL using a non-owner, non-superuser app role; verify cross-user isolation.
- Validate Compose startup and API/database lifecycle.
- Integrate action-specific authorization and caller context into Brain before sensitive generation/tool actions.
- Verify shared security persistence and secret-vault integration before multi-worker or production use.

External AI endpoints remain optional; no credential values belong in source control.

## Validation record

No tests were run while authoring the web application update. Committed tests and database-dependent behavior remain unverified; no passing result is claimed.

**Migration integrity warning:** A prior task update accidentally replaced and restored `services/api/db/migrations/0001_initial_schema.sql` with content that may not preserve the original migration. Review and correct that migration before treating Phase 1 database deliverables as complete.

## Phase sequence

See [PHASE_PLAN.md](PHASE_PLAN.md) for the approved 12-phase sequence and integration gates.

## Approval and boundaries

See [DEPENDENCY_MAP.md](DEPENDENCY_MAP.md), [AGENT_ASSIGNMENTS.md](AGENT_ASSIGNMENTS.md), and [interfaces/SHARED_PROTOCOLS.md](interfaces/SHARED_PROTOCOLS.md) for module-contract dependencies and boundary rules. The current documentation notes frontend framework/toolchain details remain an architecture decision; this implementation uses the existing repository React/Vite setup rather than selecting a new shared architecture.
