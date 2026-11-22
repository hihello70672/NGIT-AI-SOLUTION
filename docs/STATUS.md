# Project status — Phases 1–3

Status reflects files confirmed committed on `main`. Checked-in implementation and test source do not prove that tests or runtime checks passed.

## Phase 1 — Repository foundation, architecture and local data environment

**Built:** Repository overview and layout; system architecture, module dependency map, phase plan and agent assignments; shared and module interface contracts; PostgreSQL 16 Compose service, health check, persistent data volume and local application-role bootstrap; example environment configuration; Docker operations guidance; PostgreSQL schema migrations and reference data; schema ERD and database test runner/documentation. Migrations define the `ngit` schema and domain tables, harden tenant-safe message ownership and add supporting indexes; seed data is deterministic and non-secret.

**Remains:** Run ordered migrations and database checks against a fresh disposable PostgreSQL instance using separate migration and non-owner application roles. Confirm role grants, RLS behavior and migration compatibility in execution. Connect and validate the application against the database, then continue planned product phases and integrations. Source Compose and migration files are not evidence the environment has started or been validated.

**Blockers / caveats:** No database checks, migrations, Compose lifecycle or runtime checks were run for this update. Compose bootstrap creates a separate local app login but does not grant schema/object access; migration provisioning and grants remain required. Do not use production or valuable data for checks.

## Phase 2 — Authentication, security, users and web foundation

**Built:** API authentication and user endpoints, validated request/response schemas and PostgreSQL-backed user services; process-local opaque bearer-token authentication, allow-list RBAC and policy checks, owner checks, exact-scope one-time approvals, restricted-action checks, redacted audit events, emergency stop and environment-backed secret lookup. The web app includes login and registration, an authenticated responsive dashboard, profile management, Brain chat, Agent tasks and an API-backed administrator user list. API, security and UI test source is committed.

**Remains:** Execute API, security, UI and build checks; validate API/web integration and database-backed user flows. Replace or appropriately persist process-local authentication, approval, audit, emergency-stop and task state before multi-worker or durable production use. Configure deployment secrets (including password peppers) through secret management, review browser token storage, and complete production hardening.

**Blockers / caveats:** Process-local security/task state is not durable or suitable for multi-worker deployment. Browser local storage does not itself provide an authorization boundary; server-side checks remain authoritative. Deployment secrets and validated runtime integrations are still needed.

## Phase 3 — NGIT Brain, model runtime, memory and knowledge

**Built:** Brain intent recognition, confidence handling, orchestration, model registry and priority-based routing, bounded generation parameters, timeout handling, OpenAI-compatible local/self-hosted runtime adapter and explicitly optional configured self-hosted fallback. Deterministic offline intent classification provides a baseline; no external API is required. Evaluation and API tests cover intent examples, model selection, fallback, validation, sanitized errors and API behavior.

Private Memory services persist conversations, ordered messages and typed user memories using the existing `ngit.conversations`, `ngit.messages`, and `ngit.memories` schema. Database operations use authenticated server-derived user UUIDs, owner-bound SQL predicates, transaction-local RLS identity and composite parent/owner constraints. Retrieval ranks lexical matches and optionally merges vector hits only after intersecting them with that caller's authorized memory corpus. The embedding vector adapter is optional and provider-agnostic; the existing schema has no embedding column, so persistent embeddings are not claimed. Knowledge ingestion normalizes and chunks caller-provided text, stores source/chunk provenance, and requires an explicit server-configured exact-origin allow-list for verified ingestion. It performs no URL fetch and does not establish that content is factually authentic. Privacy regression tests cover cross-owner filtering, parent ownership, strict source checks and early rejection of malformed identities.

**Remains:** Run Brain evaluation/API tests, memory/privacy tests and the broader API suite; exercise configured local/self-hosted runtimes and API integration. Integrate authenticated caller authorization before exposing generation to untrusted callers. Model registry and runtime configuration remain process-local; durable model administration and persisted embeddings require a future approved storage/interface integration. Validate DB/RLS behavior with a disposable PostgreSQL instance and non-owner role.

**Blockers / caveats:** Tests and runtime/database checks have not been verified as run for this update; no passing results are claimed. Confidence is a heuristic classifier score, not factual correctness or answer quality. Provider fallback is opt-in/server-configured and does not silently require an external AI API. URL allow-list verification proves only an exact permitted origin, not source content authenticity; ingestion does not fetch URLs. Existing Brain authorization and process-local configuration caveats remain.

## Verification

Tests, builds, migrations, database checks, Compose lifecycle and runtime checks have **not been run for this update**. No passing results are claimed. Test source and schema declarations are not evidence of execution or a validated deployment.
