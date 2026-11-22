# Project status — Phases 1–3

Status is based on files present in the reviewed default-branch tree. The implementation and documentation described below are committed. Unless explicitly recorded as executed, tests and runtime checks have not been run; checked-in test sources do not establish execution or passing outcomes.

## Phase 1 — Foundation, architecture, database and local environment

**Built and committed:** Repository layout for web client, FastAPI service, database, documentation and Docker guidance; architecture, dependency map, phase plan, agent assignments, ERD, shared protocols and module interface documents; PostgreSQL 16 Compose service and environment templates; five ordered database migration files (`0001`–`0005`) defining the `ngit` schema, reference seeds, domain tables, indexes, forced row-level security (RLS), tenant constraints and tenant-safe video-source relationship. SQL assertions, a runner and database setup guidance are present.

**Remaining:** Apply migrations to a fresh PostgreSQL instance; verify migration lifecycle, grants and RLS/tenant isolation using a non-owner, non-superuser application role without `BYPASSRLS`; validate Compose startup and environment configuration.

**Blockers/caveats:** Database and Compose behavior has not been verified. RLS checks require a distinct application role and transaction-local `ngit.user_id` derived from authenticated server context. Provider metadata is not a place for secrets; external AI is optional.

## Phase 2 — Authentication, security, API, users and web client

**Built and committed:** FastAPI application/configuration, identity and user services, REST schemas/endpoints, request IDs and safe error handling; PostgreSQL caller context; process-local bearer-token authentication/revocation, role/owner policy enforcement, scoped approvals, restricted-action authorization, emergency stop, redacted audit, and environment-backed secret lookup. The React/TypeScript/Vite client provides sign-in/registration, authenticated dashboard, profile settings, read-only administrator listing, responsive/accessibility states and a shared typed API client. Backend, security, integration and web test sources and setup guidance are committed.

**Remaining:** Run backend and frontend suites; build the production frontend; exercise PostgreSQL-backed identity, authorization, cross-user isolation and local end-to-end startup. Record exact commands and outcomes only after execution.

**Blockers/caveats:** No test, build, migration, Compose lifecycle or live integration checks are claimed for this status update. Authentication tokens, approvals, emergency-stop state and audit events are process-local and lost on restart; run one API worker until durable shared state is implemented and verified. Environment secret lookup is development-oriented; browser storage is not an authorization boundary.

## Phase 3 — NGIT Brain, model runtime, memory and knowledge

**Built and committed:** Typed Brain requests/results and runtime contracts; deterministic offline heuristic intent recognition with confidence scoring; bounded asynchronous reasoning/generation orchestration; process-local model registry with capability filtering, enablement, priority routing and explicit model selection; OpenAI-compatible HTTP runtime for explicitly configured local/self-hosted endpoints; optional explicitly configured self-hosted fallback, cancellation/timeout bounds and sanitized generation failures; model listing and generation REST routes; evaluation tests for intents, confidence, routing, fallback, limits, URLs and API contract. Memory/knowledge implementation provides owner-scoped persistence interfaces, lexical retrieval, optional injected owner/type-filtered vector search, provenance-aware chunking and URL-origin allowlisting without fetching sources.

**Remaining:** Run Brain and backend evaluation suites; test configured local/self-hosted endpoints, timeouts, malformed responses and safe failures. Integrate authenticated caller authorization before exposing generation to untrusted callers. Validate memory/knowledge persistence, retrieval and user isolation against PostgreSQL and appropriate application roles. Embeddings are not persisted.

**Blockers/caveats:** Brain registry and endpoint configuration are process-local. No model endpoint or test/runtime check is reported as executed. Generation route authentication/authorization is not yet integrated: do not expose it to untrusted callers. Heuristic confidence is not a measure of factual correctness. Optional self-hosted fallback does not make third-party APIs a core dependency.

## Validation record

No tests or runtime checks have been run for this status update. No passing result is claimed for Python/API tests, web tests/build, PostgreSQL migrations/RLS, Compose startup or end-to-end integration. Test sources are not execution evidence. Do not add `docs/TEST_REPORT.md` until tests have actually run; include exact commands, environment and observed outcomes.

## Next work

1. Provision disposable PostgreSQL and distinct migration/application roles; apply ordered migrations and execute documented SQL/RLS assertions.
2. Run documented backend and frontend test commands, investigate failures, and build the production frontend.
3. Validate Compose lifecycle and local API/web operation against PostgreSQL; review authorization and tenant isolation.
4. Record exact validation evidence after execution. Implement durable shared security state before multi-worker operation.

Phases 1–3 are implemented in part and documented, but remain unvalidated and incomplete as delivery milestones.
