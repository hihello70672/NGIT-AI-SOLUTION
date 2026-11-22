# Project status — Phases 1–4

Status is based on committed files in the reviewed `main` tree. Checked-in tests are source coverage only. Tests and runtime checks have not been run for this update; no passing result is claimed.

## Phase 1 — Foundation, architecture, database and local environment

**Built and committed:** Repository layout includes `apps/web`, `services/api`, `infra/docker`, database migrations/tests, and architecture documentation. Local PostgreSQL Compose configuration and root `.env.example` are present. Five ordered SQL migrations (`0001`–`0005`) create the isolated `ngit` schema, users, roles, conversations/messages, typed memories, billing, optional provider metadata, media/video/presentation metadata, audit logs, indexes and forced RLS. Seed data and transactional SQL integration checks cover selected tenant isolation and constraints.

**Remaining validation:** Apply migrations on a fresh PostgreSQL 16+ instance; validate schema, indexes and seeds; run isolation checks using a provisioned application role that is neither superuser nor table owner; verify migration/application grants; validate Compose/local startup.

**Caveats:** Migrations run lexically as a privileged migration principal. Do not run tenant checks as superuser or table owner. Provision a separate non-owner/non-superuser application role without `BYPASSRLS`; grant only required privileges. API code sets `ngit.user_id` transaction-locally only from authenticated server context, never client input. Provider metadata stores opaque credential references, not secrets. External AI remains optional. No database/Compose checks are claimed as run.

## Phase 2 — Authentication, security, API, users and web client

**Built and committed:** FastAPI configuration, request IDs, safe errors, auth/user services, REST schemas/routes, server-enforced authorization and transaction-local database caller context. Security primitives include expiring/revocable bearer tokens, policy/ownership checks, approval/emergency-stop controls, redacted audit events and environment secret lookup. React/TypeScript/Vite client includes sign-in/registration, authenticated dashboard shell, profile settings and administrator user list; responsive dark design system with green accents and Inter typography; shared API client with loading, empty, error/retry, expired-session, and backend access-denied states. User-management listing is read-only and authorization remains backend-enforced. UI tests cover auth errors, registration mode, profile updates/logout, admin denial, list loading/error/retry/empty/populated states, and expired sessions.

**Remaining:** Execute backend/frontend suites, production build, PostgreSQL API integration and end-to-end local startup; review security and database role behavior.

**Caveats:** Example peppers require local non-example secrets. Token, approval, emergency-stop and audit state are process-local; use a single worker until shared durable state exists. Environment lookup is not production secret management. Browser local-storage bearer tokens are not an authorization boundary.

## Phase 3 — Brain, model runtime, memory and knowledge

**Built and committed:** Brain has deterministic intent classification, bounded generation and local/self-hosted runtime routing. Memory exposes authenticated owner-scoped conversations/messages, typed memories, lexical retrieval, optional owner-scoped vector candidate reranking, provenance-aware chunked knowledge ingestion and URL-origin allowlisting without remote fetch. Vector embeddings/indexing are optional adapters; schema persists no embedding column/vector extension. External AI APIs remain optional.

**Remaining/caveats:** Tests/database checks not run; vector loader must honor owner scope and embeddings are not persisted. Allowlisting validates origin, not content. Brain caller authorization and process-local state retain documented caveats.

## Phase 4 — Personal Agent

**Built and committed:** `services/api/modules/agent/` provides explicit-goal planning, allowlisted tool registry, synchronous task execution, observations/verification and owner-scoped process-local task history. Filesystem operations are workspace-confined, UTF-8/size-limited; writes require approval and read-back verification. Browser inspection uses injected HTTP(S) reader; navigation requires approval and configured adapter. Computer control only invokes injected adapter; actions require approval. Sensitive capabilities use shared `RestrictedActionManager`, policy engine, emergency stop and `ApprovalEngine`, rejecting when approval/verification fails. Authenticated routes expose tools, task submission/history/read, grant requests/reviewer decisions, resume/reject. Adapters/workspace opt-in; external AI not required.

**Validation outstanding:** Phase 4 and existing API suites have not run for this update. No passing results, live browser/network, deployed filesystem security, desktop control, database integration, or multi-worker behavior are claimed. Task history and approval state are process-local; execution synchronous, not a durable queue.

**Boundaries:** Grant request is not approval. Shared engine requires distinct reviewer; requesters cannot self-approve. Never mount routes without authenticated caller dependency and explicit workspace config. Filesystem containment is not an OS sandbox; deployment isolation and symlink/race hardening need review. Browser adapter must enforce network/SSRF policy beyond URL parsing. Computer adapter intentionally not bundled.

## Validation record

No tests or runtime checks are claimed as executed for this update, including Python/API/agent tests, SQL migration/RLS, Compose, frontend tests/build or live adapters. Record exact commands, environment and outcomes only after running them.

## Next work

Execute documented API/web suites and resolve failures. Complete PostgreSQL migration/RLS checks with a non-owner role; validate grants, lifecycle, durable shared state and production startup. Review workspace deployment isolation and browser SSRF controls before multi-worker or untrusted deployment. Preserve distinct-reviewer approval for sensitive actions.

Agent suite command from repository root: `PYTHONPATH=. python -m pytest services/api/tests` with documented dependencies installed. No test result is implied.
