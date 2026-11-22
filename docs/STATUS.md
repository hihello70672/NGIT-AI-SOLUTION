# Project status — Phases 1–3

This status records repository evidence, not proof of runtime behavior. Tests have **not been run in this task**; no passing result is claimed.

## Phase 1 — Foundation, architecture, database, local environment

Foundation documentation, Docker Compose PostgreSQL service, ordered SQL migrations, seed data, schema checks, and ERD are committed. The `ngit` schema includes users and roles, user-scoped conversations, messages, memory, billing, optional provider configuration, media/video and presentation metadata, audit logs, supporting indexes, composite ownership constraints, and row-level security policies for user-owned tables. Migration `0003` records role-assignment RLS hardening.

Database migration tooling remains deliberately plain ordered SQL. Apply all files in `services/api/db/migrations/` lexicographic order on a fresh PostgreSQL 16+ database. Database/RLS tests and Compose lifecycle still require execution. API database integration also requires validation; migration presence does not establish that the API uses the schema.

## Phase 2 — Authentication, security, API, user management, web foundation

The API has FastAPI configuration, authentication and user services, shared security primitives, and security regression tests. `services/api/security.py` provides opaque expiring/revocable in-process bearer tokens using keyed digests; default-deny role-based policy checks and resource-owner enforcement; distinct-approver, expiring, single-use approvals bound to actor/action/resource; restricted action authorization with audited denials; recursively filtered audit events; fail-closed emergency stop; environment-backed secret lookup; and safe security error payloads. Process-local token, approval and audit state is not durable or cross-worker safe; shared production persistence remains a deployment requirement.

`services/api/app.py` authenticates requests to the existing Brain router at its boundary, while memory and optional agent endpoints use the shared bearer dependency. Authentication endpoint integration, database-backed security/audit behavior, API/web test execution, and deployment validation remain to be verified. The web foundation exists only under `apps/web`; external AI APIs remain optional.

## Phase 3 — Brain, memory, retrieval, knowledge

`services/api/modules/brain` provides deterministic intent/confidence handling, typed generation orchestration, model registry/routing, and bounded local/self-hosted OpenAI-compatible runtime configuration. The Brain API is protected by a router-level bearer authentication dependency; additional action-specific authorization and production deployment validation remain necessary.

`services/api/modules/memory` provides authenticated conversations/messages, profile/preference/fact/summary memory, deterministic lexical retrieval, an optional owner-filtered vector-search adapter contract, source-allowlisted knowledge ingestion, URL origin verification, and chunk/source metadata. Ownership is derived from bearer authentication and enforced by database transaction-local RLS, SQL filters, and existing composite keys. Vector storage/embeddings remain intentionally unpersisted; knowledge ingestion accepts source text and does not fetch URLs or assert truth.

## Remaining validation and integration

- Run API/unit and web suites and record exact commands/outcomes.
- Run SQL migrations and RLS tests on disposable PostgreSQL using a non-owner, non-superuser application role; verify cross-user isolation.
- Validate Compose startup and API/database lifecycle.
- Integrate action-specific authorization and caller context into Brain before enabling sensitive generation/tool actions for untrusted callers.
- Keep source allowlists restricted to approved knowledge sources; any vector persistence architecture requires existing approval.
- Verify durable shared security stores and secret-vault integration before multi-worker/production use.

External AI endpoints remain optional; no credential values belong in source control.

## Validation record

No tests were run while authoring this update. Committed tests and database-dependent behavior remain unverified; no passing result is claimed.
