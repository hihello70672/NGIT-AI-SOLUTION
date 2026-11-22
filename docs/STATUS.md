# Project status — Phases 1–4

Status is based on files present in the reviewed `main` tree. Tests and runtime checks are only reported as executed when actually run; checked-in test sources do not establish passing results.

## Phase 1 — Foundation and data layer

**Built:** Repository foundation and architecture/dependency/interface documentation; PostgreSQL 16 local Compose service with health check and persistent volume; environment example with placeholders; database ERD, ordered SQL migrations, reference seed data, schema assertions and runner. Compose currently starts PostgreSQL only; it does not start API or web containers.

**Remains:** Execute and validate migrations and SQL assertions against PostgreSQL; verify Compose startup/lifecycle; review schema constraints and tenant isolation under real database roles and grants. Tests and runtime checks have not been run for this status update; no pass is claimed.

**Blockers/caveats:** Database grants, non-owner row-level-security behavior and migration execution remain unverified. A running PostgreSQL service and configured local environment are needed for these checks.

## Phase 2 — Authentication, backend security, users, and web

**Built:** Backend authentication and user services/API, password verification, opaque bearer tokens, server-derived roles, authenticated REST boundaries and ownership checks. Security code includes policy/RBAC checks, approval decisions with reviewer separation and single-use exact-scope grants, restricted-action gates, emergency stop, redacted audit events and environment-backed secret lookup. The React/TypeScript/Vite web app includes sign-in and registration, responsive workspace, overview, Brain chat, Personal Agent tasks, profile settings, read-only administrator user listing, backend API integrations and UI test sources. API and frontend READMEs document setup and operational caveats.

**Remains:** Run backend and frontend test suites and frontend build; exercise API/database integration; validate authentication, authorization, ownership and approval end-to-end; conduct deployment/security review. No tests or runtime checks have been run for this work, and no passing result is claimed.

**Blockers/caveats:** Security tokens, approvals, emergency-stop state and audit events are process-local, not durable or shared between workers; use a single worker until shared persistence is implemented and verified. Configure deployment-specific random token/password peppers instead of example placeholders. Agent workspace confinement is not an OS sandbox, and browser URL syntax validation is not an SSRF/network boundary. External AI APIs are optional.

## Phase 3 — Brain, model runtime, memory, knowledge

**Built:** Deterministic offline intent recognition, confidence thresholds, typed contracts, bounded generation, in-process model registry, deterministic routing, local/self-hosted OpenAI-compatible runtime, optional self-hosted fallback and sanitized failures. Memory uses the existing owner-scoped conversations/messages/memories schema and transaction-local database identity; retrieval checks the authenticated owner's corpus and requested memory type before returning lexical or optional vector hits. Knowledge ingestion chunks caller-provided text, retains provenance, and checks exact URL origins against an allowlist without fetching remote content. Optional vector search uses injected embeddings and owner-scoped candidate-loading adapters. Authenticated memory API derives owner identity from context. Phase 3 implementation and test source files are present in the reviewed tree.

**Remains:** Run Brain, memory, database and API tests; validate migrations, grants and non-owner RLS; verify generation authorization before exposing it to untrusted callers. Embeddings are not persisted.

**Blockers/caveats:** Optional vector integration depends on a trusted candidate loader enforcing owner/type filters; retrieval independently rejects candidates outside its loaded owner corpus. URL allowlisting does not establish remote-content authenticity or safety and does not replace SSRF/network protections in a fetching adapter. No memory, database or runtime tests were run for this status update; no pass is claimed.

## Phase 4 — Personal Agent

**Built:** Deterministic fail-closed task planning; explicit typed tool allowlist; process-local owner-scoped task history; browser inspection/navigation, bounded workspace text filesystem and injected computer-control interfaces; tool observations and verification; authenticated task, history, approval request/decision, resume and rejection endpoints. Sensitive browser navigation, filesystem writes and computer-control actions use shared policy and restricted-action approval with exact task-step resource scopes, separate reviewer decisions and single-use grants. External adapters are optional and loaded only through explicit environment-configured module/callable specifications; no shell/OS-control tool is exposed. Agent unit and API test sources cover planning/registry, filesystem bounds, approval gating and resume, mismatched scopes, ownership, adapters, browser/computer interfaces and API review flow.

**Remains:** Run Agent/backend tests and runtime checks. Browser adapters need deployment-level DNS/IP/redirect/response-size protections; computer adapters must provide their own constrained authorization and execution boundary. Review approval lifecycle against the deployment's shared-state design before multi-worker use.

**Blockers/caveats:** Workspace path confinement is not an OS sandbox and does not eliminate symlink/race risks. Task records and approvals are in-memory, not durable/shared; use a single worker. No tests, builds, migrations, Compose startup or other runtime checks were run for this status update; test source presence is not evidence of passing tests.

## Verification record

No tests, builds, migrations, Compose startup, or other runtime checks were run for this status update. The repository contains test source files, but their presence is not evidence that tests pass.
