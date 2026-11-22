# Project status — Phases 1–2

Status reflects files confirmed committed on `main` in the repository. Checked-in implementation and test source do not prove that tests or runtime checks passed.

## Phase 1 — Repository foundation, architecture and local data environment

**Built:** Repository overview and layout; system architecture, module dependency map, phase plan and agent assignments; shared and module interface contracts; PostgreSQL 16 Compose service, health check, persistent data volume and local application-role bootstrap; example environment configuration; Docker operations guidance; PostgreSQL schema migrations and reference data; schema ERD and database test runner/documentation. The migrations define the `ngit` schema and domain tables, harden tenant-safe message ownership and add supporting indexes; seed data is deterministic and non-secret.

**Remains:** Run the ordered migrations and database checks against a fresh disposable PostgreSQL instance using separate migration and non-owner application roles. Confirm role grants, RLS behavior and migration compatibility in execution. Connect and validate the application against the database, and continue the planned product phases and integrations. Compose and database source files being committed are not evidence that the environment has been started or validated.

**Blockers / caveats:** No database checks, migrations, Compose lifecycle or runtime checks were run for this update. The Compose bootstrap creates a separate local app login but does not grant schema/object access; migration provisioning/grants are still required. Do not use production or valuable data for checks.

## Phase 2 — Authentication, security, users and web foundation

**Built:** API authentication and user endpoints, validated request/response schemas and PostgreSQL-backed user services; process-local opaque bearer-token authentication, allow-list RBAC and policy checks, owner checks, exact-scope one-time approvals, restricted-action checks, redacted audit events, emergency stop and environment-backed secret lookup. The web app includes login and registration, an authenticated responsive dashboard, profile management, Brain chat, Agent tasks and an API-backed administrator user list. API, security and UI test source is committed.

**Remains:** Execute the API, security, UI and build checks; validate API/web integration and database-backed user flows. Replace or appropriately persist process-local authentication, approval, audit, emergency-stop and task state before multi-worker or durable production use. Configure deployment secrets (including password peppers) through secret management, review browser token storage and complete production hardening.

**Blockers / caveats:** Process-local security/task state is not durable or suitable for multi-worker deployment. Browser token storage is local storage and does not itself provide an authorization boundary; server-side checks remain authoritative. The UI administrator view is convenience only. Configured deployment secrets and validated runtime integrations are still needed.

## Verification

Tests, builds, migrations, database checks, Compose lifecycle and runtime checks have **not been run for this update**. No passing results are claimed.
