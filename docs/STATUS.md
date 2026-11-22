# Project status — Phases 1–3

This status records repository evidence, not proof of runtime behavior. Tests have **not been run in this task**; no passing result is claimed.

## Phase 1 — Foundation, architecture, database, local environment

Foundation documentation, Docker Compose PostgreSQL service, ordered SQL migrations, seed data, schema checks, and ERD are committed. The `ngit` schema includes users and roles, user-scoped conversations, messages, memory, billing, optional provider configuration, media/video and presentation metadata, audit logs, supporting indexes, composite ownership constraints, and row-level security policies for user-owned tables. Migration `0003` hardens role-assignment RLS.

Database migration tooling remains deliberately plain ordered SQL. Apply all files in `services/api/db/migrations/` lexicographic order on fresh PostgreSQL 16+. Database/RLS tests and Compose lifecycle still require execution. Migration presence does not establish that the API uses the schema.

## Phase 2 — Authentication, security, API, user management

The API now provides environment-backed FastAPI configuration, database pool lifecycle, validated registration/login/logout and caller-owned profile routes, request IDs, safe validation/conflict/internal error handling, and authenticated Brain router access. User records and role lookups use the PostgreSQL services through the existing pool and transaction-local RLS user context. Password verification uses scrypt with a configurable pepper; opaque expiring/revocable token digests, default-deny authorization, approval controls, and audit are defined in `security.py` and the auth service.

Security token/approval/audit state remains process-local; only a single worker is supported until a shared adapter is approved and implemented. Background-task support remains an in-process interface, not durable execution. Existing REST is request/response; no WebSocket is justified by current module contracts, so none was added. External AI APIs remain optional. OpenAPI is provided by FastAPI.

## Phase 3 — Brain, memory, retrieval, knowledge

Brain, memory and deterministic retrieval modules are present. Brain endpoints have router-level bearer authentication. Memory queries derive ownership from the authenticated context and use database transaction-local RLS where applicable. Knowledge ingestion accepts source text and enforces configured source allowlists; URL fetching is not implemented. Vector persistence/embeddings are intentionally absent pending architecture approval.

## Remaining validation and integration

- Run API/unit and web suites and record exact commands/outcomes.
- Run SQL migrations and RLS tests on disposable PostgreSQL with a non-owner, non-superuser app role; verify cross-user isolation.
- Validate Compose startup and API/database lifecycle.
- Integrate action-specific authorization and caller context into Brain before sensitive generation/tool actions.
- Verify shared security persistence and secret-vault integration before multi-worker or production use.

External AI endpoints remain optional; no credential values belong in source control.

## Validation record

No tests were run while authoring this update. Committed tests and database-dependent behavior remain unverified; no passing result is claimed.
