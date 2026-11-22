# Project status — Phases 1–3

This status records repository evidence, not proof of runtime behavior. Tests have **not been run in this task**; no passing results are claimed.

## Phase 1 — Foundation, architecture, database, local environment

Foundation documentation, Docker Compose PostgreSQL service, ordered SQL migrations, seed data, schema checks, and ERD are committed. The `ngit` schema includes users and roles, user-scoped conversations, messages, memory, billing, optional provider configuration, media/video and presentation metadata, audit logs, supporting indexes, composite ownership constraints, and row-level security policies for user-owned tables. Migration `0003` records the role-assignment RLS hardening.

Database migration tooling remains deliberately plain ordered SQL; no ORM or migration framework was introduced. Apply all files in `services/api/db/migrations/` lexicographic order to a fresh PostgreSQL 16+ database. Database/RLS test behavior and Compose lifecycle still require execution against disposable PostgreSQL. Application DB integration also requires validation; migration presence does not establish that the API uses the schema.

## Phase 2 — Authentication, security, API, user management, web foundation

FastAPI configuration, authentication and user services, shared security primitives, tests, and React/TypeScript web foundation are present. Security state is process-local and is not production multi-worker durable without shared persistence.

## Phase 3 — Brain, memory, retrieval, knowledge

Committed `services/api/modules/brain` provides deterministic intent/confidence handling, typed generation orchestration, model registry/routing, and timeout-bounded local/self-hosted OpenAI-compatible runtime configuration. Brain REST routes remain unauthenticated and must not be exposed to untrusted users until caller authentication/authorization integration is completed.

Committed `services/api/modules/memory` provides authenticated conversations/messages, profile/preference/fact/summary memory, deterministic lexical retrieval, an optional owner-filtered vector-search adapter contract, source-allowlisted knowledge ingestion, URL origin verification, and chunk/source metadata. Ownership is derived from bearer authentication and enforced by database transaction-local RLS, SQL filters, and existing composite keys. Vector storage/embeddings are deliberately not persisted: the established schema has no vector field or extension; embedding-backed search remains optional and requires caller-provided embeddings and an authorized candidate loader. Knowledge ingestion accepts source text and does not fetch URLs or assert truth.

`services/api/tests/test_memory.py` includes service ownership, SQL scoping, vector isolation/non-finite score filtering, ingestion verification/chunking, and optional embedding adapter checks. No test commands were run during this update; API, security, database/RLS, and end-to-end integration remain unverified.

## Remaining validation and integration

- Run API/unit and web suites; record exact commands/outcomes.
- Run SQL migrations and RLS tests against disposable PostgreSQL using a non-owner, non-superuser application role; validate cross-user isolation.
- Validate Docker Compose startup and API/database lifecycle.
- Integrate authenticated caller context into Brain before exposing generation to untrusted callers; address process-local state for production deployments.
- Configure only approved knowledge source allowlists and decide any later vector persistence architecture through the existing approval process.

External AI endpoints remain optional; no credential values belong in source control.

## Phase 1 validation record

No tests were run while authoring this update. Committed tests and database-dependent behavior remain unverified; no passing result is claimed.
