# Project status — Phases 1–2

This status records repository evidence. Tests have not been run in this task, and no passing result is claimed.

## Phase 1 — Foundation, architecture, database, and local environment

**Built/committed:** Repository foundation and architecture documentation, the approved phase plan and module boundaries, local PostgreSQL Docker Compose setup and usage documentation, environment examples, ordered SQL migrations and seed data, database schema checks/tests, and ERD documentation. The database schema covers users and roles, user-scoped conversations/messages/memory, billing, optional provider configuration, media/presentation metadata, audit logs, indexes, ownership constraints, and row-level security; migration `0003` hardens role-assignment RLS.

**Remaining:** Execute migrations on a fresh PostgreSQL 16+ database, run schema/RLS tests using a non-owner, non-superuser application role, verify cross-user isolation, and validate Compose startup and database lifecycle. Confirm the API's database integration against the migrations rather than inferring it from file presence.

**Blocker/risk:** Migration integrity is unresolved. A prior task accidentally replaced and restored `services/api/db/migrations/0001_initial_schema.sql` with content that may not preserve the original migration. Review and correct it against the intended schema before treating Phase 1 database deliverables as complete. The SQL migrations are deliberately plain ordered SQL; apply them lexicographically.

## Phase 2 — Authentication, security, API, and user management

**Built/committed:** The FastAPI service includes versioned registration/login/logout and current-user profile endpoints, protected Brain routes, memory and optional agent integration, request validation/IDs, safe error handling, password hashing, expiring/revocable bearer tokens, default-deny role and ownership checks, approval and audit primitives, and user-management services. The API uses PostgreSQL-backed identity services and transaction-local user context for RLS. API/security tests and usage documentation are present.

**Remaining:** Run API/unit and live database integration tests; verify migration compatibility, authentication persistence, transaction-local RLS context, cross-user access isolation, and complete authorization on sensitive Brain/tool actions. Token/approval/audit state remains process-local and supports only a single worker until an approved shared persistent adapter is implemented. Background tasks are in-process, not durable. Configure password/token peppers through environment secrets before deployment; no real secrets belong in source control.

**Blocker/risk:** External AI integrations are optional and unconfigured. Shared persistence for security state and durable background execution are not implemented. Confirm action-specific authorization and caller context before enabling sensitive generation or tool actions. Existing endpoints are request/response; no WebSocket was added.

## Validation record

Tests have not been run in this task. API, database/RLS, and web test results remain unverified; no passing result is claimed. Compose startup and migration runtime behavior have also not been verified here.

## Phase sequence and boundaries

See [PHASE_PLAN.md](PHASE_PLAN.md) for the approved 12-phase delivery sequence and integration gates. See [DEPENDENCY_MAP.md](DEPENDENCY_MAP.md), [AGENT_ASSIGNMENTS.md](AGENT_ASSIGNMENTS.md), and [interfaces/SHARED_PROTOCOLS.md](interfaces/SHARED_PROTOCOLS.md) for module dependencies and boundary rules.

## Note

The repository contains later-phase web implementation, but this document's status scope is phases 1–2. The web app's tests were not run either. Migration-integrity warning above remains the concrete known blocker for accepting Phase 1 database work.
