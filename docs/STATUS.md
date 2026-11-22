# Project status — Phases 1–4

Status is based on committed files in the reviewed `main` tree. Checked-in tests are source coverage only. Tests and runtime checks have not been run for this update; no passing result is claimed.

## Phase 1 — Foundation, architecture, database and local environment

**Built and committed:** Repository layout includes `apps/web`, `services/api`, `infra/docker`, database migrations/tests, and architecture documentation. Local PostgreSQL Compose configuration and root `.env.example` are present. Four ordered migrations (`0001`–`0004`), reference seed data, schema checks and migration instructions are present. The schema covers user-scoped conversations/messages and memories with row-level security, billing, provider/media metadata, audit logs and indexes.

**Remaining:** Apply migrations to fresh PostgreSQL 16+; check integrity, constraints, seeds and indexes; exercise RLS/tenant isolation with a provisioned application role; validate Compose/local startup.

**Caveats:** SQL tests require schema/table creation privileges and do not provision the non-owner role needed for forced RLS checks. Configure a separate non-owner, non-superuser role without `BYPASSRLS`, plus application grants. Migration ledger is in `public` while application tables are in `ngit`; verify grants and ownership. No database or Compose checks are claimed.

## Phase 2 — Authentication, security, API, users and web client

**Built and committed:** FastAPI configuration, request IDs, safe errors, auth/user services, REST schemas/routes, server-enforced authorization and transaction-local database caller context. Security primitives include expiring/revocable bearer tokens, policy/ownership checks, approval/emergency-stop controls, redacted audit events and environment secret lookup. React/TypeScript/Vite client includes sign-in/registration, authenticated dashboard, profile settings, admin user list and shared API client, with checked-in tests.

**Remaining:** Execute backend/frontend tests, production build, PostgreSQL API integration and end-to-end local startup; review security and database role behavior.

**Caveats:** `AUTH_TOKEN_PEPPER` and `PASSWORD_PEPPER` require non-example secrets meeting minimum lengths. Token, approval, emergency-stop and audit state are process-local; use one worker until shared durable state is implemented and validated. Environment lookup is not production secret-manager integration. User-list endpoint is read-only. Browser local-storage bearer tokens are not an authorization boundary.

## Phase 3 — Brain, model runtime, memory and knowledge

**Built and committed:** Brain offers deterministic intent classification, bounded generation and local/self-hosted runtime routing; Memory provides authenticated owner-scoped conversations/messages, typed memories, lexical retrieval, optional owner-scoped vector candidate reranking, provenance-aware chunked knowledge ingestion and URL-origin allowlisting without remote fetching. Existing schema constraints, transaction-local PostgreSQL RLS context, authenticated REST and privacy tests are used. Vector embeddings/indexing are optional adapters; the schema has no embedding column/vector extension. External AI APIs remain optional.

**Remaining and caveats:** Tests/database checks have not been run; RLS remains unproven until checked with non-owner grants/role. Vector loader must honor owner scope and embeddings are not persisted. Allowlisting checks source origin only, not content. Brain caller authorization and process-local state retain documented caveats.

## Phase 4 — Personal Agent

**Built and committed:** `services/api/modules/agent/` provides deterministic explicit-goal planning, an allowlisted tool registry, synchronous task execution, observations/verification and owner-scoped process-local task history. Filesystem operations are restricted to a configured workspace, UTF-8 and size-limited; writes require approval and read-back verification. Browser inspection accepts HTTP(S) through an injected reader, while navigation requires approval and a configured adapter. Computer control has no shell/OS implementation and only invokes an injected adapter; its actions require approval. All sensitive capabilities are checked through the shared `RestrictedActionManager`, policy engine, emergency stop and `ApprovalEngine`: missing approval pauses before the handler, grants match the exact action/resource and are consumed once, and rejection/verification failures cannot succeed. Authenticated routes expose tools, task submission/history/read, grant request, reviewer decision through the shared engine, resume and rejection. Browser/computer adapters and workspace are opt-in; external AI APIs are unnecessary. Unit/API tests are checked in.

**Validation outstanding:** Phase 4 and existing API suites have not been executed for this update. No passing result, live browser/network access, deployed filesystem security, desktop control, database integration or multi-worker behavior is claimed. Task history and security/approval state are process-local; execution is synchronous, not a durable queue.

**Boundaries:** Requesting a grant is not approving it. The shared engine enforces a distinct reviewer, and API requester cannot self-approve. The authenticated reviewer decision route delegates to that engine. Do not mount routes without authenticated caller dependency and explicit workspace configuration. Filesystem containment is not an OS-level sandbox; symlink/race hardening and deployment isolation need runtime review. Browser adapters must enforce network/SSRF policy; URL parsing alone is insufficient. Computer-control adapter is intentionally not bundled.

## Validation record

No tests or runtime checks are claimed as executed for this update: this includes Python API/agent tests, SQL migration/RLS, Compose, frontend tests/build and live adapters. Record exact commands, environment and outcomes only after running them.

## Next work

Run the documented Python suite and resolve failures; run frontend checks/build and validate backend integration. Complete PostgreSQL migration/RLS checks with a non-owner role; validate grants, durable shared state, lifecycle, filesystem isolation and browser SSRF controls before multi-worker or untrusted deployment. Preserve separation-of-duties approval for every sensitive action.

Agent suite command from repository root: `PYTHONPATH=. python -m pytest services/api/tests` with documented dependencies installed. No test result is implied here.
