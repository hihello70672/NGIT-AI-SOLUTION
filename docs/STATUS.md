# Project status — Phases 1–3

Status is based on files present in the reviewed default-branch tree. Tests and runtime checks are only reported as executed when actually run; checked-in tests do not establish a passing result.

## Phase 1 — Foundation and data layer

**Built:** Repository foundation, architecture and dependency/interface documentation, PostgreSQL 16 local Compose service with health check and persistent volume, environment example with placeholders, database ERD, five ordered SQL migrations, reference seed data, database assertions and runner. The schema includes tenant-isolation measures and documented migration guidance. Compose currently starts PostgreSQL only; it does not start API or web containers.

**Remains:** Execute and validate migrations and SQL assertions against PostgreSQL; verify Compose startup and lifecycle; review schema constraints and tenant isolation under real database roles and grants. Tests and runtime checks have not been run for this status update, so no pass is claimed.

**Blockers/caveats:** Database grants, non-owner row-level-security behavior and migration execution remain unverified. A running PostgreSQL service and configured local environment are needed for these checks.

## Phase 2 — Authentication, backend security, users, and web

**Built:** Backend authentication and user services/API, including password verification, opaque bearer tokens, server-derived roles, authenticated REST boundaries and ownership checks. Security code includes policy/RBAC checks, approval decisions with reviewer separation and single-use exact-scope grants, restricted-action gates, emergency stop, redacted audit events and environment-backed secret lookup. The React/TypeScript/Vite web app includes sign-in and registration, responsive workspace, overview, Brain chat, Personal Agent tasks, profile settings, read-only administrator user listing, backend API integrations and UI test sources. API and frontend READMEs document setup and operational caveats.

**Remains:** Run backend and frontend test suites and frontend build; exercise API/database integration; validate authentication, authorization, ownership and approval behavior end-to-end; conduct deployment/security review. No tests or runtime checks have been run for this work, and no passing result is claimed.

**Blockers/caveats:** Security tokens, approvals, emergency-stop state and audit events are process-local and are not durable or shared between workers; deploy a single worker until approved shared persistence is implemented and verified. Configure deployment-specific random token/password peppers rather than example placeholders. Agent filesystem workspace confinement is not an OS sandbox, and browser URL syntax validation is not an SSRF/network boundary. External AI APIs are optional.

## Phase 3 — Brain, model runtime, memory, knowledge

**Built:** Deterministic offline intent recognition, confidence thresholds, typed contracts, bounded generation, in-process model registry, deterministic routing, local/self-hosted OpenAI-compatible runtime, optional self-hosted fallback and sanitized failures. Memory uses the existing owner-scoped conversations/messages/memories schema and transaction-local database identity; retrieval checks the authenticated owner's corpus and requested memory type before returning lexical or optional vector hits. Knowledge ingestion chunks caller-provided text, retains source provenance, and verifies exact URL origins against an allowlist without fetching remote content. Vector search is optional and uses injected embedding and owner-scoped candidate loading adapters. Memory API routes derive owner identity from authenticated context. Privacy and isolation test sources cover memory writes/reads, vector hits and source verification.

**Remains:** Run runtime/database checks and tests. Generation authorization remains a separate boundary that must be integrated/tested before exposure to untrusted callers; embeddings are not persisted. Database migration execution, grants and non-owner RLS behavior are not verified.

**Blockers/caveats:** Optional vector integration depends on a trusted candidate loader enforcing owner/type filters; the retrieval layer independently rejects candidates outside its loaded owner corpus. URL allowlisting is not proof remote content is authentic or safe and does not replace SSRF/network protections in any fetcher. No memory, database or runtime tests were run for this update; no passing result is claimed.

## Verification record

No tests, builds, migrations, Compose startup, or other runtime checks have been run for this update. Existing test sources are present in the repository, but their results are unknown.
