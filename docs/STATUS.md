# Project status — Phases 1–3

This status records repository evidence, not proof of runtime behavior. Tests have **not been run in this task**; no passing results are claimed.

## Phase 1 — Foundation, architecture, database, local environment

Foundation documentation, Docker Compose PostgreSQL service, schema migrations, seed data, schema checks, and ERD are committed. Schema defines user-scoped conversations, messages, memory records, composite owner keys, and row-level security policies. Compose/migration/RLS behavior still requires execution against disposable PostgreSQL.

## Phase 2 — Authentication, security, API, user management, web foundation

FastAPI configuration, authentication and user services, shared security primitives, tests, and React/TypeScript web foundation are present. Security state is process-local and is not production multi-worker durable without shared persistence.

## Phase 3 — Brain, memory, retrieval, knowledge

Committed `services/api/modules/brain` provides deterministic intent/confidence handling, typed generation orchestration, model registry/routing, and timeout-bound local/self-hosted OpenAI-compatible runtime configuration. Brain REST routes remain unauthenticated and must not be exposed to untrusted users until caller authentication/authorization integration is completed.

Committed `services/api/modules/memory` provides authenticated conversations/messages, profile/preference/fact/summary memory, deterministic lexical retrieval, an optional owner-filtered vector-search adapter contract, source-allowlisted knowledge ingestion, URL origin verification, and chunk/source metadata. Memory router is mounted in `services/api/app.py`; ownership is derived from bearer authentication and enforced by database transaction-local RLS, SQL filters, and existing composite keys. Vector storage/embeddings are deliberately not persisted because the established schema has no vector field or extension; embedding-backed search is optional and requires a caller-provided embedding and authorized candidate loader. Knowledge ingestion accepts source text and does not fetch URLs or assert truth.

`services/api/tests/test_memory.py` includes service ownership, SQL scoping, vector isolation/non-finite score filtering, ingestion verification/chunking, and optional embedding adapter checks. No test commands were run during this update; API, security, database/RLS, and end-to-end integration are unverified.

## Remaining validation and integration

- Run API/unit and web suites, record exact commands/outcomes.
- Run SQL migrations and RLS tests against disposable PostgreSQL using a non-owner application role; validate cross-user isolation.
- Validate Docker Compose startup and API/database lifecycle.
- Integrate authenticated caller context into Brain before exposing generation to untrusted callers; address process-local state for production deployments.
- Configure only approved knowledge source allowlists and decide any later vector persistence architecture through the existing approval process.

External AI endpoints remain optional; no credential values belong in source control.

## Phase 3 validation record

No tests were run while authoring this update. The committed tests and database-dependent behaviors remain unverified; no passing result is claimed.
