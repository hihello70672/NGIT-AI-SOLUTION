# Project status — Phases 1–4

Status is based on files present in the reviewed `main` tree. Checked-in tests are source coverage only. Tests and runtime checks have not been run for this update; no passing result is claimed.

## Phase 1 — Foundation, architecture, database and local environment

**Built and committed:** Repository layout includes `apps/web`, `services/api`, `infra/docker`, database migrations/tests, and architecture documentation. Five ordered SQL migrations (`0001–0005`) define the isolated `ngit` schema, users, roles, conversations/messages, typed memories, billing, optional provider metadata, media/video/presentation metadata, audit logs, indexes, forced RLS, and tenant-safe video-source constraints. Seed data and transactional SQL assertions cover selected isolation and constraints. Architecture, dependency, phase, assignment, ERD, shared-interface, and status docs exist.

**Remaining:** Apply migrations to fresh PostgreSQL 16+; validate grants and isolation with a provisioned application role that is neither owner nor superuser; verify migration/application grants and Compose startup.

**Caveats:** Migration execution is privileged. Tenant checks must not run as a superuser or table owner. Configure a separate non-owner/non-superuser role without `BYPASSRLS`; grant only required privileges. API must set `ngit.user_id` transaction-locally from authenticated server context. Provider metadata stores opaque credential references, never secrets. External AI remains optional. Database and Compose behavior remain unverified.

## Phase 2 — Authentication, security, API, users and web client

**Built and committed:** FastAPI configuration, request IDs, safe errors, auth/user services, REST schemas/routes, backend authorization, and transaction-local database caller context are reported present. Security primitives include expiring/revocable opaque bearer tokens, role-checked allow-list policy and owner checks, exact-scope expiring approval engine with separation of duties and atomic consumption, restricted-action manager, emergency stop, redacted audit events and environment-backed secret lookup. Agent approval decisions require explicit admin permission and a reviewer distinct from the task owner. React/TypeScript/Vite includes sign-in/registration, authenticated dashboard, profile settings, read-only administrator listing, responsive design and shared API client. Security and API test sources cover engine and route boundaries.

**Remaining:** Run backend/frontend test suites, production frontend build, PostgreSQL-backed API integration and end-to-end local startup; review security and database role behavior.

**Caveats:** Authentication tokens, approvals, emergency-stop state and audit state are process-local; operate a single worker until shared durable state exists. Environment lookup is not production secret management. Browser local-storage bearer tokens are not an authorization boundary. No test or runtime result is claimed as run.

## Phase 3 — Brain, model runtime, memory and knowledge

**Built and committed:** Brain supports deterministic offline intent recognition and confidence thresholds, typed request/response contracts, bounded generation, in-process model registry, deterministic priority routing, local/self-hosted OpenAI-compatible runtimes, optional self-hosted fallback and sanitized failures. Server environment configures runtimes; external AI APIs are optional. Evaluation tests cover intents, confidence, routing, local generation, opt-in fallback, validation and safe failures. Memory/knowledge provides authenticated owner-scoped conversations/messages and typed memory persistence on the existing schema, deterministic lexical retrieval, optional injected owner/type-filtered vector search, provenance-aware text chunking, and exact URL-origin allowlisting without fetching sources. Privacy-focused tests cover owner binding, foreign conversation rejection, retrieval filtering, schema use and source verification.

**Remaining:** Run Python tests and database checks; validate RLS/vector-loader ownership; assess classifier/model quality with representative evaluation data. Durable model administration is future work.

**Caveats:** Intent confidence represents classifier certainty, not factual correctness or response quality. Generation authorization remains a separate integration concern. Origin allowlisting does not validate fetched content; embeddings are not persisted by the current schema.

## Phase 4 — Personal Agent

**Built and committed:** Deterministic single-step task planner; explicit tool allowlist/registry; process-local owner-scoped task history; task execution and observation/verification. Browser inspection/navigation, workspace-bounded UTF-8 text filesystem access, and injected computer-control adapter interfaces exist. Filesystem writes, browser navigation, and computer actions use shared restricted-action policy, emergency stop, and exact-scope single-use approvals. Task owners may request grants but cannot decide them; authenticated reviewers with `admin.approval.decide`/`agent.approval.decide` authorization decide through the shared engine. Resume consumes the exact approval for the current pending task; rejection and verification failure fail closed. Authenticated REST endpoints expose tools, submission, owner-scoped history/detail, approval request, reviewer decision, resume and reject. Unit and API test sources cover planning, registry, path boundaries, approvals, reviewer separation, exact resume, verification failure, ownership and rejection.

**Remaining:** Run documented Python/API suites and runtime checks.

**Caveats:** Task records and approval/security state are process-local and not durable; operate a single worker. Filesystem path checks are not an OS sandbox and do not eliminate symlink/race risks; deployment isolation is required. Browser URL syntax validation is not SSRF/network safety: adapters must enforce allowed origins, DNS/IP restrictions, redirects and response limits. Computer control requires an explicitly injected constrained adapter. No external AI API is used by this deterministic engine.

## Validation record

No tests or runtime checks have been run for this update. This includes Python/API, SQL migration/RLS, Compose, frontend tests/build, and live integration. Checked-in test sources do not establish execution or passing outcomes.

## Next work

Run documented API/web suites and resolve failures. Complete PostgreSQL migration/RLS checks with the non-owner role, verify grants/lifecycle and local end-to-end startup. Review authorization boundaries and design durable shared state before multi-worker operation. Record exact commands, environment and outcomes only after validation.

Documented Python command (not reported as run):

```bash
PYTHONPATH=. python -m pytest services/api/tests
```

Database integration tests require a disposable PostgreSQL instance; see `services/api/db/tests/README.md`.
