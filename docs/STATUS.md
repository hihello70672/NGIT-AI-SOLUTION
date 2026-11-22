# Project status — Phases 1–4

Status is based on files present in the reviewed `main` tree. Tests and runtime checks have not been run for this update unless explicitly stated below. Checked-in test sources are not evidence of execution.

## Phase 1 — Foundation, architecture, database and local environment

**Built and committed:** Repository layout includes `apps/web`, `services/api`, `infra/docker`, database migrations/tests, and architecture documentation. Five ordered SQL migrations (`0001–0005`) define the isolated `ngit` schema, users, roles, conversations/messages, typed memories, billing, optional provider metadata, media/video/presentation metadata, audit logs, indexes, forced RLS and tenant-safe video-source constraints. Seed data and transactional SQL assertions cover selected isolation and constraints. Architecture, dependency, phase, assignment, ERD, status and shared-interface docs exist.

**Remaining:** Apply migrations to fresh PostgreSQL 16+; validate grants and isolation with an application role that is neither owner nor superuser and lacks `BYPASSRLS`; verify grants and Compose startup.

**Caveats:** Migration execution is privileged. Tenant checks must not run as a superuser or table owner. API sets `ngit.user_id` transaction-locally from authenticated server context on user-scoped identity reads and writes. Provider metadata stores opaque credential references, never secrets. External AI remains optional. Database and Compose behavior have not been verified.

## Phase 2 — Authentication, security, API, users and web client

**Built and committed:** FastAPI configuration, request IDs, safe error envelopes, password-backed auth, user service, REST schemas/routes, backend authorization, and transaction-local database caller context. Security includes expiring/revocable opaque bearer tokens, allow-list policy/owner checks, exact-scope expiring approvals with separation of duties and atomic consumption, restricted-action manager, emergency stop, redacted audit events and environment-backed secret lookup. The React/TypeScript/Vite client includes sign-in/registration, authenticated dashboard, profile settings and read-only administrator listing. Backend unit/HTTP/security test sources exist, along with an opt-in PostgreSQL identity integration suite.

**Remaining:** Run backend/frontend suites and production frontend build; run PostgreSQL-backed API integration and end-to-end local startup; review database role behavior and security.

**Caveats:** Auth tokens, approvals, emergency-stop state and audit events are process-local; run a single worker until durable shared persistence exists. Environment lookup is not production secret management. Browser local-storage bearer tokens are not an authorization boundary. No test or runtime result is claimed as run. The database-backed API test is skipped unless `NGIT_TEST_DATABASE_URL` points to a disposable migrated database and suitable non-owner/non-superuser role.

## Phase 3 — Brain, model runtime, memory and knowledge

**Built and committed:** Brain supports deterministic offline intent recognition, confidence thresholds, typed contracts, bounded generation, in-process model registry, deterministic routing, local/self-hosted OpenAI-compatible runtimes, optional self-hosted fallback and sanitized failures. External AI APIs are optional. Memory/knowledge provides authenticated owner-scoped conversations/messages and typed memory persistence, lexical retrieval, optional injected owner/type-filtered vector search, provenance-aware chunking and exact URL-origin allowlisting without fetching sources.

**Remaining:** Run Python tests and database checks; validate RLS/vector-loader ownership and model quality.

**Caveats:** Intent confidence is not factual correctness. Generation authorization is separate. Origin allowlisting does not validate fetched content; embeddings are not persisted.

## Phase 4 — Personal Agent

**Built and committed:** Deterministic task planner, explicit tool registry, process-local owner-scoped tasks, execution observation and verification. Browser, workspace-bounded filesystem and injected computer-control interfaces exist. Sensitive actions use shared policy, emergency stop and exact-scope approvals; reviewer decisions require admin authorization and separation from task owner. Authenticated REST endpoints expose task and approval lifecycle.

**Remaining:** Run documented Python/API suites and runtime checks.

**Caveats:** Task and security state are process-local; use a single worker. Filesystem checks are not an OS sandbox. Browser adapters still need SSRF/network protections; computer control requires a constrained injected adapter.

## Validation record

No tests or runtime checks have been run for this update. This includes Python/API, SQL migration/RLS, Compose, frontend tests/build and live integration. The opt-in PostgreSQL API integration tests were added but have not been executed.

## Next work

Run documented API/web suites and resolve failures. Complete PostgreSQL migration/RLS checks with the non-owner role, verify grants/lifecycle and local end-to-end startup. Review authorization boundaries and design durable shared state before multi-worker operation. Record exact commands, environment and outcomes only after validation.

Documented Python command (not reported as run):

```bash
PYTHONPATH=. python -m pytest services/api/tests
```

Database integration tests require a disposable PostgreSQL instance; see `services/api/db/tests/README.md` and `services/api/tests/README.md`.
