# Project status — Phases 1–3

This status records repository evidence, not proof of runtime behavior. Tests have **not been run in this task**; no passing result is claimed.

## Phase 1 — Foundation, architecture, database, local environment

Foundation documentation, Docker Compose PostgreSQL service, ordered SQL migrations, seed data, schema checks, and ERD are committed. The `ngit` schema includes users and roles, user-scoped conversations, messages, memory, billing, optional provider configuration, media/video and presentation metadata, audit logs, supporting indexes, composite ownership constraints, and row-level security policies for user-owned tables. Migration `0003` hardens role-assignment RLS.

Database migration tooling remains deliberately plain ordered SQL. Apply all files in `services/api/db/migrations/` lexicographic order on fresh PostgreSQL 16+. Database/RLS tests and Compose lifecycle still require execution. Migration presence does not establish that the API uses the schema.

## Phase 2 — Authentication, security, API, user management

The FastAPI service exposes configured versioned REST endpoints for registration, login, logout, current-user profile read/update, protected Brain endpoints, memory, and optional agent integration. Request validation, request IDs, safe error handling, OpenAPI, password hashing, opaque expiring/revocable bearer tokens, role and ownership policies, approvals, and audit primitives are included. User identity persistence is implemented through PostgreSQL-backed services and the existing connection pool with transaction-local user context for RLS-scoped access. Password and token peppers must be configured in the environment; no real secrets are committed.

Token/approval/audit state remains process-local; only a single worker is supported until an approved shared adapter exists. Background-task support is an in-process interface, not durable execution. Existing endpoints are request/response, so no WebSocket was justified or added. External AI APIs remain optional. Tests and live database integration have not been executed in this task.

## Phase 3 — Brain, memory, retrieval, knowledge

Brain, memory and deterministic retrieval modules are present. Brain endpoints have router-level bearer authentication. Memory queries derive ownership from authenticated context and use database transaction-local RLS where applicable. Knowledge ingestion accepts source text and enforces configured source allowlists; URL fetching is not implemented. Vector persistence/embeddings are intentionally absent pending architecture approval.

## Remaining validation and integration

- Run API/unit and web suites and record exact commands/outcomes.
- Run SQL migrations and RLS tests on disposable PostgreSQL with a non-owner, non-superuser app role; verify cross-user isolation.
- Validate Compose startup and API/database lifecycle.
- Integrate action-specific authorization and caller context into Brain before sensitive generation/tool actions.
- Verify shared security persistence and secret-vault integration before multi-worker or production use.

External AI endpoints remain optional; no credential values belong in source control.

## Validation record

No tests were run while authoring this update. Committed tests and database-dependent behavior remain unverified; no passing result is claimed.
