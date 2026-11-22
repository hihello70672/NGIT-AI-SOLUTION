# Project status — Phases 1–4

Status is based on the committed files in the reviewed `main` tree. Checked-in tests are source coverage only. Tests and runtime checks have not been run for this update; no passing result is claimed.

## Phase 1 — Foundation, architecture, database, local environment

**Built and committed:** Repository layout includes `apps/web`, `services/api`, `infra/docker`, database migrations and tests, and architecture documentation. Local PostgreSQL Compose configuration (`compose.yaml`) and root `.env.example` are present. Documentation covers architecture, dependencies, phase plan, assignments, shared protocols, and Brain/Memory/Agent interfaces. Four ordered migrations (`0001`–`0004`), reference seed data, schema checks and migration instructions are present. The schema covers user-scoped conversations/messages and memories with row-level security, billing, provider metadata, media/video/presentation metadata, audit logs, and indexes.

**Remaining:** Apply migrations to fresh PostgreSQL 16+; check migration integrity, schema constraints, seeds and indexes; exercise RLS/tenant isolation with a provisioned application role; validate Compose/local startup.

**Blockers and caveats:** SQL test migration role needs schema/table creation privileges and does not establish a non-owner application role for forced RLS checks. Provision a separate non-owner, non-superuser role without `BYPASSRLS`. Migration `0001` creates `ngit` but does not grant application schema/table privileges; configure grants out of band. Migration ledger is in `public`, separate from application tables; verify ownership and grants. No database or Compose checks are claimed.

## Phase 2 — Authentication, security, API, users and web client

**Built and committed:** FastAPI includes validated configuration, request IDs, safe errors, authentication/user services, REST routes/schemas, server-enforced authorization and transaction-local database caller context. Security primitives include expiring/revocable bearer tokens, role/ownership policies, approval/emergency-stop controls, redacted audit events and environment-backed secret lookup. React/TypeScript/Vite client includes sign-in/registration, authenticated dashboard, profile settings, admin user-list flow and shared API client, with checked-in API/security/config/UI tests.

**Remaining:** Execute backend and frontend suites, frontend production build, API integration against configured PostgreSQL, and end-to-end local startup. Review security and database role behavior in runtime.

**Caveats:** `AUTH_TOKEN_PEPPER` and `PASSWORD_PEPPER` must be supplied as non-example secrets meeting documented minimum lengths. Token, approval, emergency-stop and audit state are process-local; keep deployment single-worker until durable shared state and lifecycle are implemented and validated. Environment secret lookup is not production secret-manager integration. User-list endpoint is read-only; admin account creation, role mutation and deletion are not provided. Browser bearer-token local storage is not an authorization boundary.

## Phase 3 — Brain, model runtime, memory and knowledge

**Built and committed:** Brain services include deterministic intent classification, bounded generation, local/self-hosted runtime routing and safe orchestration. Memory services implement authenticated user-owned conversations, ordered messages, typed short-/long-term memories, lexical retrieval, optional owner-scoped vector reranking, chunked knowledge ingestion with provenance, and URL-origin allowlist verification without remote fetching. Existing schema constraints, transaction-local PostgreSQL RLS context, authenticated REST routes and privacy-focused tests are used. Vector embeddings/indexing remain optional adapters because the approved schema has no embedding column or vector extension; returned vector hits are constrained through the authenticated owner's memory corpus. External AI APIs are optional.

**Remaining and caveats:** Tests and database/runtime integration have not been run. RLS remains unproven without the configured non-owner role and grants. Vector adapter requires trusted owner-scoped candidate loading and does not persist embeddings. Source allowlisting checks origin only; it does not fetch/authenticate remote content. Brain caller authorization and process-local model/security state retain documented caveats.

## Phase 4 — Personal Agent

**Built and committed:** `services/api/modules/agent/` implements deterministic explicit-goal planning, an allowlisted tool registry, synchronous task execution, observations and verification, and owner-scoped process-local task history. Filesystem operations are confined to the configured workspace, UTF-8 and bounded; writes require approval and are read-back verified. Browser inspection accepts HTTP(S) URLs through an injected reader; navigation requires approval and an explicitly configured adapter. Computer control has no shell/OS implementation and can call only a configured adapter; all such actions require approval. Sensitive actions use shared `RestrictedActionManager`, `PolicyEngine`, emergency stop and `ApprovalEngine`; missing approval pauses before the side effect, exact action/resource binding and one-time grant consumption are enforced, and rejection/verification failures do not report success. Authenticated routes expose tools, task submission/history/read, pending-grant request, reviewer decision through shared approval engine, resume and rejection. Browser/computer adapters and workspace are opt-in; external AI APIs are not required. Agent unit/API tests are checked in.

**Validation still outstanding:** Phase 4 and existing API test suites have not been executed for this update. No passing result, live browser/network access, filesystem deployment security, desktop control, database integration or multi-worker behavior is claimed. The task store, approval engine and security state are process-local, and task execution is synchronous; deploy a single worker and do not treat this as a durable background queue.

**Boundaries:** A user can request an approval grant but cannot self-approve it: the shared approval engine requires a distinct reviewer. Reviewers must use the authenticated decision route/approval engine. Do not mount agent endpoints without authenticated caller dependency and explicit workspace configuration. The filesystem sandbox is a workspace boundary, not an OS-level sandbox against a compromised process; symlink/race hardening and deployment filesystem isolation require runtime review. Browser adapters must enforce network/SSRF policy; URL syntax validation alone does not guarantee safe network access. Computer-control adapter is intentionally not bundled.

## Validation record

No tests or runtime checks are claimed as executed for this update. This includes Python API/agent tests, SQL migration/RLS checks, Compose startup, frontend tests/build and live adapter checks. Record exact commands, environment and outcomes only after running them.

## Next work

Run the documented Python test command and resolve failures; run frontend checks/build and validate backend integration. Complete PostgreSQL migration/RLS checks using a non-owner role; validate deployment grants, durable shared security/agent state, lifecycle, filesystem and browser SSRF controls before multi-worker or untrusted deployment. Preserve approval separation-of-duties for every sensitive action.

For the agent suite run from repository root: `PYTHONPATH=. python -m pytest services/api/tests` with documented dependencies installed. No test result is implied here.
