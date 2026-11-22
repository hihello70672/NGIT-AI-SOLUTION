# Project status — Phases 1–4

This status records implementation evidence only. Tests have not been run in this task; no passing result is claimed.

## Phase 1 — Foundation, architecture, database, local environment

**Built/committed:** Repository foundation and architecture documentation, approved phase plan and module boundaries, local PostgreSQL Docker Compose setup and usage docs, environment examples, ordered SQL migrations and seed data, database schema checks/tests, and ERD documentation. The schema covers users/roles, user-scoped conversations/messages/memory, billing, optional provider configuration, media/presentation metadata, audit logs, ownership constraints, and row-level security; migration `0003` hardens role-assignment RLS.

**Remaining:** Execute migrations against fresh PostgreSQL 16+; run schema and RLS tests with a non-owner, non-superuser role; verify cross-user isolation, Compose lifecycle, and API/database integration.

**Blocker/risk:** The migration integrity warning regarding `0001_initial_schema.sql` remains unresolved; review the restored file against intended schema before accepting Phase 1.

## Phase 2 — Authentication, security, API, users

**Built/committed:** Versioned FastAPI routes for register/login/logout and current-user profile read/update, with the existing server-side opaque token and RBAC/approval services wired to PostgreSQL-backed user records. Caller identity and active status/roles are reloaded server-side per request. Passwords use scrypt and a deployment-injected pepper; request schemas reject unknown fields; safe errors and request correlation IDs are standardized. Existing Brain routes require authenticated callers. The psycopg adapter applies `ngit.user_id` transaction-locally for user-scoped SQL. Existing module services and task interface are retained; background tasks remain synchronous/in-process and no unjustified WebSocket was added. OpenAPI describes the REST interface. API/config/database tests were added or extended; tests have not been executed.

**Runtime boundaries:** Opaque tokens, approvals, emergency-stop state, and audit events are process-local, not durable or multi-worker safe. Use one worker only until approved persistence is introduced. Deployment must set unique strong `AUTH_TOKEN_PEPPER` and `PASSWORD_PEPPER` secrets; no secret is committed. `/health` checks process liveness only, not database readiness.

**Remaining:** Run API/security unit tests; validate migrations and user transactions on disposable PostgreSQL, including transaction-local RLS context and cross-user isolation; review sensitive Brain/tool authorization; exercise full startup and web/API integration. External AI integrations stay optional.

**Blocker/risk:** Shared durable security-state storage and production secrets management are undecided. Do not treat current process-local security state as durable.

## Phase 3 — Brain, runtime, memory, knowledge

**Built/committed:** Existing modular Brain, memory, runtime, and API modules remain in place; implementation details and evidence are tracked in their module docs and test sources.

**Remaining:** Run runtime, evaluation, API, ownership, and database/RLS validation as scheduled by the phase gate.

## Phase 4 — Personal Agent

**Built/committed:** Existing Agent module and shared security approval engine are preserved; current execution/task behavior is documented as synchronous and in-process where applicable.

**Remaining:** Run Agent/API tests and verify adapters, authorizations, and approvals in the provisioned environment.

## Validation record

Tests were not run for this status update. API, security, database/RLS, web, and integration outcomes remain unverified; no passing result is claimed. The restored migration integrity warning, startup behavior, database connection and configured local/self-hosted model endpoint behavior also remain to be verified.

## Phase sequence and boundaries

See [PHASE_PLAN.md](PHASE_PLAN.md) for the approved delivery sequence. Do not introduce WebSockets or durable task claims without the corresponding approved contract and implementation evidence.

## Note

The repository contains later-phase web implementation, but this status scope records Phases 1–4. The migration-integrity warning above remains a concrete blocker for accepting Phase 1 database work.

## Phase 3 implementation record

The Brain runtime and deterministic evaluation suite were already present at the reviewed repository HEAD. This status preserves the distinction between committed implementation and unverified runtime/test behavior.

## Phase 4 implementation record

The Personal Agent implementation extends the existing agent module and shared security approval engine. Tool actions are explicit; the planner does not infer arbitrary commands. Approval requests require a distinct reviewer, and a matching grant is consumed once. Task history and approval state remain process-local; execution is synchronous and not a durable worker.

## Phase 2 security implementation note

Security primitives are for a single-process development deployment only. In-memory token revocation, emergency-stop state, approvals, and audit events are not durable or restart/multi-worker safe. Set `AUTH_TOKEN_PEPPER` (at least 32 bytes) and `PASSWORD_PEPPER` (at least 16 bytes) through deployment secret injection; never commit real values. `.env.example` intentionally does not include usable authentication pepper values. Audit redaction is defense in depth; callers must not pass sensitive data.

API routes are documented in OpenAPI at `/openapi.json` and `/docs`. The database connection uses transaction-local identity context for RLS. Tests are source coverage only until executed; no result is asserted.

Tests were not run for this status update.
