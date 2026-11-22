# Project status — Phases 1–4

Status is based on files present in the reviewed `main` tree. Checked-in tests are source coverage only. Tests and runtime checks have not been run for this update; no passing result is claimed.

## Phase 1 — Foundation, architecture, database and local environment

**Built and committed:** Repository layout includes `apps/web`, `services/api`, `infra/docker`, database migrations/tests, and architecture documentation. Five ordered SQL migrations (`0001`–`0005`) define the isolated `ngit` schema, users, roles, conversations/messages, typed memories, billing, optional provider metadata, media/video/presentation metadata, audit logs, indexes and forced RLS. Seed data and transactional SQL integration checks cover selected tenant isolation and constraints. Architecture, dependency, phase, assignment, ERD and shared-interface documentation are present.

**Remaining:** Apply migrations to fresh PostgreSQL 16+; validate schema, indexes, seed data and isolation with a provisioned application role that is neither superuser nor table owner; verify migration/application grants and Compose lifecycle/local startup.

**Blockers/caveats:** Migration execution is privileged. Tenant checks must not run as superuser or table owner. Provision a separate non-owner/non-superuser role without `BYPASSRLS` and grant only required privileges. API code must set `ngit.user_id` transaction-locally from authenticated server context. Provider metadata stores opaque credential references, not secrets. External AI remains optional. Database and Compose behavior remain unverified.

## Phase 2 — Authentication, security, API, users and web client

**Built and committed:** FastAPI configuration, request IDs, safe errors, auth/user services, REST schemas/routes, backend-enforced authorization and transaction-local database caller context are present. Security primitives include expiring/revocable bearer tokens, policy/ownership checks, approval/emergency-stop controls, redacted audit events and environment-secret lookup. React/TypeScript/Vite includes sign-in/registration, authenticated dashboard, profile settings, read-only administrator user listing, responsive design system and shared API client. Backend and frontend test sources are present.

**Remaining:** Run backend/frontend suites, production build, PostgreSQL-backed API integration and end-to-end local startup; review security and database-role behavior.

**Blockers/caveats:** Replace example peppers with local secrets. Token, approval, emergency-stop and audit state is process-local; use one worker until shared durable state exists. Environment lookup is not production secret management. Browser local-storage bearer tokens are not an authorization boundary. Runtime checks and suites have not been run.

## Phase 3 — Brain, model runtime, memory and knowledge

**Built and committed:** Brain supports deterministic offline intent recognition and confidence thresholds, typed request/response contracts, bounded generation, in-process model registry, deterministic priority routing, local/self-hosted OpenAI-compatible runtimes, optional self-hosted fallback and sanitized failures. Server environment configures runtimes; external AI APIs are optional. Evaluation tests cover intents, confidence, routing, local generation, opt-in fallback, validation and safe failures. Memory/knowledge provides authenticated owner-scoped conversations/messages and typed-memory persistence on the existing schema, deterministic lexical retrieval, optional injected owner/type-filtered vector search, bounded provenance-aware text chunking and exact URL-origin allowlisting without fetching sources. Privacy-focused tests cover owner binding, foreign-conversation rejection, retrieval filtering, schema use and source verification.

**Remaining:** Run Python tests and database checks; validate RLS/vector-loader ownership; assess classifier/model quality with representative evaluation data. Durable model administration is future work.

**Caveats:** Intent confidence measures classifier certainty, not factual correctness or response quality. Generation authorization remains a separate integration/security concern. Do not expose generation to untrusted callers until authorization is integrated and tested. Origin allowlisting does not verify fetched content; embeddings are not persisted by the current schema.

## Phase 4 — Personal Agent

**Built and committed:** Deterministic single-step task planner, explicit tool allowlist/registry, process-local owner-scoped task history, task execution and observation/verification. Browser inspection/navigation, workspace-bounded UTF-8 text filesystem access and injected computer-control adapter interfaces are provided. Filesystem writes, browser navigation and computer actions are sensitive and are paused behind the shared `RestrictedActionManager`, policy engine, emergency stop and exact-scope single-use approval engine. Task owners may request grants but cannot decide them; a distinct authenticated reviewer decides through the shared engine, and resumption consumes the exact approved grant. Rejection and verification failure fail closed. Authenticated REST endpoints expose tools, submission, owner-scoped history/detail, grant requests, reviewer decisions, resume and reject. Unit and API test sources cover planning, registry, path boundaries, approvals, reviewer separation, exact resume, verification failure, task ownership and rejection.

**Remaining:** Run documented Python/API suites and runtime checks. Task records and approval/security state are process-local and not durable; operate a single worker until shared lifecycle/state is designed and validated. Filesystem path checks are not an OS sandbox and do not eliminate symlink/race risks; deployment isolation is required. Browser URL syntax validation is not SSRF/network safety: any adapter must enforce allowed origins, DNS/IP restrictions, redirects and response limits. Computer control has no built-in OS implementation and requires an explicitly injected, constrained adapter. External AI APIs are not used by this deterministic engine.

## Validation record

No tests or runtime checks have been run for this update. This includes Python/API, SQL migration/RLS, Compose, frontend tests/build and live integration checks. Checked-in tests are not evidence of execution or passing results.

## Next work

Run documented API/web suites and resolve failures. Complete PostgreSQL migration/RLS checks with the non-owner role, validate grants/lifecycle and local end-to-end startup. Review authorization boundaries and design durable shared state before multi-worker use. Record exact commands, environment and outcomes only after validation.

Documented Python command (not reported as run):

```bash
PYTHONPATH=. python -m pytest services/api/tests
```

Database integration tests require a disposable PostgreSQL instance; see `services/api/db/tests/README.md`.
