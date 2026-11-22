# Project status — Phases 1–4

Status reflects files confirmed committed on `main`. Source/test presence does not establish that tests or runtime checks passed.

## Phase 1 — Repository foundation, architecture and local data environment

**Built:** Repository overview and layout; architecture, dependency map, phase plan and agent assignments; shared and module interface contracts; PostgreSQL 16 Compose service, health check, persistent data volume and local application-role bootstrap; example environment configuration; Docker operations guidance; PostgreSQL schema migrations and reference data; schema ERD and database test runner/documentation. Migrations define the `ngit` schema and domain tables, tenant-safe message ownership and supporting indexes; seed data is deterministic and non-secret.

**Remains:** Run ordered migrations and database checks against a fresh disposable PostgreSQL instance using separate migration and non-owner application roles. Confirm role grants, RLS behavior and migration compatibility in execution. Connect and validate the application against the database, then continue planned product phases and integrations. Compose bootstrap creates a separate local app login but does not grant schema/object access; migration provisioning and grants remain required. Do not use production or valuable data for checks.

**Caveats:** No database checks, migrations, Compose lifecycle or runtime checks were run for this update.

## Phase 2 — Authentication, security, users and web foundation

**Built:** API authentication and user endpoints, validated request/response schemas and PostgreSQL-backed user services; process-local opaque bearer-token authentication, allow-list RBAC and policy checks, owner checks, exact-scope one-time approvals, restricted-action checks, redacted audit events, emergency stop and environment-backed secret lookup. The web app includes login and registration, authenticated responsive dashboard, profile management, Brain chat, Agent tasks and API-backed administrator user list. API, security and UI test source is committed.

**Remains:** Execute API, security, UI and build checks; validate API/web integration and database-backed user flows. Replace or appropriately persist process-local authentication, approval, audit, emergency-stop and task state before multi-worker or durable production use. Configure deployment secrets (including password peppers) through secret management, review browser token storage and complete production hardening.

**Caveats:** Process-local security/task state is not durable or appropriate for multi-worker deployment. Browser local storage does not itself provide an authorization boundary; server-side checks remain authoritative. Deployment secrets and validated runtime integrations remain outstanding.

## Phase 3 — NGIT Brain, model runtime, memory and knowledge

**Built:** Brain intent recognition, confidence handling, orchestration, model registry and priority-based routing, bounded generation parameters, timeout handling, OpenAI-compatible local/self-hosted runtime adapter and explicitly optional configured self-hosted fallback. Deterministic offline intent classification provides a baseline; no external API is required. Evaluation and API test source covers intent examples, model selection, fallback, validation, sanitized errors and API behavior.

Private Memory services persist conversations, ordered messages and typed user memories using the existing `ngit.conversations`, `ngit.messages`, and `ngit.memories` schema. Database operations use authenticated server-derived user UUIDs, owner-bound SQL predicates, transaction-local RLS identity and composite parent/owner constraints. Retrieval ranks lexical matches and optionally merges vector hits only after intersecting them with the caller's authorized memory corpus. Embedding is optional/provider-agnostic; the schema has no embedding column, so persistent embeddings are not claimed. Knowledge ingestion normalizes and chunks caller-provided text, stores source/chunk provenance, and requires an explicit server-configured exact-origin allow-list for verified ingestion. It performs no URL fetch and does not establish source authenticity. Privacy regression tests cover cross-owner filtering, parent ownership, strict source checks and malformed identities.

**Remains:** Run Brain evaluation/API tests, memory/privacy tests and broader API suite; exercise configured local/self-hosted runtimes and API integration. Integrate authenticated caller authorization before exposing generation to untrusted callers. Model registry/runtime configuration remain process-local; durable model administration and persisted embeddings require a future approved storage/interface integration. Validate DB/RLS behavior with a disposable PostgreSQL instance and non-owner role.

**Caveats:** Tests and runtime/database checks have not been verified as run for the described updates; no passing results are claimed. Confidence is a heuristic classifier score, not factual correctness or answer quality. Provider fallback is opt-in/server-configured and does not silently require an external AI API. URL allow-list verification proves only an exact permitted origin, not source-content authenticity; ingestion does not fetch URLs. Existing Brain authorization and process-local configuration caveats remain.

## Phase 4 — Personal Agent, tools and approval-gated execution

**Built:** Deterministic fail-closed task planner, explicit tool registry, authenticated task submission/detail/history, execution observations and verification, and owner-filtered process-local task records. Workspace-bound UTF-8 filesystem read/write, read-only HTTP(S) inspection with injected adapter, approval-gated browser navigation, and enumerated injected computer-control actions are available. Sensitive tool execution rechecks shared policy and exact-scope one-time approval immediately before the effect; task resume rejects mismatched approval scope, requester cannot approve their own action, and rejected/failed/unverified actions do not report success. API exposes approval request/reviewer decision/resume/reject workflows using the existing approval engine. Agent unit and API test source covers planning, allow-listing, workspace boundaries, approval separation/scope, history ownership, adapters and failure verification.

**Remains:** Run Agent unit/API tests and broader API suite; validate browser/network adapter SSRF and redirect defenses, filesystem isolation against symlink/race attacks, and computer adapter constraints. Configure a workspace and explicitly reviewed adapters for runtime use. Replace process-local task/approval/security state with approved durable shared persistence before multi-worker or production deployment.

**Caveats:** Tests and runtime checks have not been verified as run for this update; no passing results are claimed. Browser URL syntax validation alone is not network/SSRF protection; injected adapters must enforce DNS/IP, redirects, response-size and network policy. Filesystem workspace checks are not an OS sandbox and do not eliminate symlink/race risks. Computer actions are limited by the injected adapter, not a general OS-control guarantee. Task/history state is process-local and not durable.

## Verification

Tests, builds, migrations, database checks, Compose lifecycle and runtime checks have **not been run for this update**. No passing results are claimed. Test source and schema declarations are not execution evidence or a validated deployment.
