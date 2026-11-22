# Project status — Phases 1–3

Status is based on files present in the reviewed `main` tree at commit `3b4ea82a2a2d53a8318a1672003661fd4a2293da`. The tree confirms the files described below are committed. Tests and runtime checks have not been run for this status update; checked-in test sources do not establish execution or passing outcomes.

## Phase 1 — Foundation, architecture, database and local environment

**Built and committed:** Repository layout and architecture documentation; PostgreSQL 16 local Compose service and environment example; five ordered migrations (`0001–0005`) defining the isolated `ngit` schema and domain tables, reference seeds, indexes, forced row-level security, and tenant-safe video-source constraints. SQL test assertions, a runner, and setup guidance are present. Architecture, dependency map, phase plan, agent assignments, ERD, shared protocols and module interface documents are committed.

**Remaining:** Apply migrations to a fresh PostgreSQL instance; verify grants and tenant isolation with an application role that is neither table owner nor superuser and lacks `BYPASSRLS`; confirm migration lifecycle and Compose startup. Run SQL assertions and record environment and outcome.

**Blockers and caveats:** Database and Compose behavior have not been verified. Migration execution is privileged; RLS validation must use the separate non-owner/non-superuser application role. The API must set `ngit.user_id` transaction-locally from authenticated server context. Provider metadata is for opaque credential references, not secrets. External AI is optional.

## Phase 2 — Authentication, security, API, users and web client

**Built and committed:** FastAPI application/configuration, request IDs, safe errors, user and authentication services, REST endpoints/schemas, PostgreSQL caller context, and backend authorization. Security primitives include expiring/revocable opaque bearer tokens, allow-list role and owner policy checks, exact-scope approvals with expiry, reviewer separation and atomic consumption, restricted-action authorization, emergency stop, redacted audit events and environment-backed secret lookup. Agent approval decisions enforce administrator policy and task-owner separation. React/TypeScript/Vite web client provides sign-in/registration, authenticated dashboard, profile settings and read-only administrator listing, with responsive/accessibility states and shared API client. Backend, database-integration, security, agent API and web UI test sources are committed.

**Remaining:** Run backend and frontend suites; build the production frontend; execute opt-in PostgreSQL-backed API integration and SQL/RLS assertions; verify end-to-end local startup. Review authorization boundaries and database role behavior; record exact commands and results only after execution.

**Blockers and caveats:** No tests or runtime checks have been run for this update, including Python/API, frontend tests/build, migration/RLS, Compose or live integration. PostgreSQL integration requires a disposable migrated database and appropriate non-owner/non-superuser role. Auth tokens, approvals, emergency-stop state and audit events are process-local: operate a single API worker until durable shared state exists. Environment lookup is not production secret management; browser local-storage bearer tokens are not an authorization boundary.

## Phase 3 — Brain, model runtime, memory and knowledge

**Built and committed:** Brain typed request/result and runtime contracts; deterministic offline intent baseline and confidence threshold; bounded generation orchestration; in-process model catalogue with capability, enablement, priority routing and explicit selection; OpenAI-compatible HTTP integration for server-configured local or self-hosted model endpoints; optional, explicit self-hosted fallback and safe generation failures; model listing and generation REST routes. Evaluation sources cover intent examples/confidence, registry routing, local generation, fallback/opt-out, malformed limits and safe API behavior. Memory/knowledge service sources provide owner-scoped persistence interfaces, lexical retrieval, optional injected owner/type-filtered vector search, provenance-aware chunking and URL-origin allowlisting without fetching sources.

**Remaining:** Execute Brain and full backend evaluation suites; validate configured local and self-hosted endpoints and failure/timeouts; integrate authenticated caller authorization before exposing generation to untrusted callers; validate persistence/isolation and optional retrieval against PostgreSQL and suitable roles. Embeddings are not persisted.

**Blockers and caveats:** No tests or runtime checks have been run for this update. Brain registry and route configuration are process-local; this is not durable model administration or multi-worker shared state. A missing local model does not silently select an external provider; fallback is explicitly configured and request-opt-in. Classifier confidence is not factual correctness or response quality. Brain API authentication integration remains a prerequisite before untrusted exposure.

## Validation record

Tests and runtime checks have not been run for this update. No passing result is claimed for Python/API tests, web tests/build, PostgreSQL migration/RLS, Compose startup or end-to-end integration.

## Next work

1. Run documented backend and frontend suites and fix failures.
2. Run migrations and SQL/RLS assertions against disposable PostgreSQL using the required non-owner/non-superuser role; verify grants and transaction-local caller context.
3. Verify Compose and local API/web startup and PostgreSQL-backed identity integration.
4. Review durable shared security state before enabling multiple API workers.
5. Run Brain tests and validate explicitly configured local/self-hosted runtimes; keep generation behind authenticated caller authorization before untrusted access.
6. Update this record with exact commands and observed outcomes after verification.

Documented backend command (not reported as run):

```bash
PYTHONPATH=. python -m pytest services/api/tests
```

Database setup and test instructions are in `services/api/db/tests/README.md` and `services/api/tests/README.md`.
