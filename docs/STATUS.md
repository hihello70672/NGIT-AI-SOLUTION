# Project status — Phases 1–3

Status is based on files present in the reviewed `main` tree. Checked-in tests are source coverage only. Tests and runtime checks have not been run for this update; no passing result is claimed.

## Phase 1 — Foundation, architecture, database, local environment

**Built and committed:** The repository layout includes `apps/web`, `services/api`, `infra/docker`, database migrations and tests, and architecture documentation. Local PostgreSQL Compose configuration (`compose.yaml`) and a root environment example (`.env.example`) are present. Documentation covers architecture, dependencies, the phase plan, assignments, shared protocols, and Brain/Memory/Agent interfaces. Database work includes the ERD, four ordered migrations (`0001`–`0004`), reference seed data, schema checks and migration instructions. The schema covers user-scoped conversations/messages and memories with row-level security, billing, provider metadata, media/video/presentation metadata, audit logs, and indexes.

**Remaining:** Apply migrations to a fresh PostgreSQL 16+ instance; check migration integrity, schema constraints, seeds and indexes; exercise RLS and tenant isolation using an explicitly provisioned application role; validate Compose/local startup.

**Blockers and caveats:** The SQL test runner's migration role needs schema/table creation privileges and does not itself establish the non-owner application role needed to prove forced RLS. Provision a separate non-owner, non-superuser role without `BYPASSRLS` for tenant-path checks. Migration `0001` creates schema `ngit` but does not grant application schema/table privileges; configure grants out of band. The migration ledger is in `public`, separate from application tables in `ngit`; verify ownership and grants separately. No database or Compose checks have been run.

## Phase 2 — Authentication, security, API, users and web client

**Built and committed:** The FastAPI application includes validated configuration, request IDs, safe error handling, authentication and user services, REST routes/schemas, server-enforced authorization and transaction-local database caller context. Security primitives include expiring/revocable bearer tokens, role and ownership policies, approval and emergency-stop controls, redacted audit events and environment-backed secret lookup. The React/TypeScript/Vite client includes sign-in/registration, authenticated dashboard, profile settings, admin user-list flow and shared API client, with checked-in API, security, configuration and UI regression tests.

**Remaining:** Execute backend and frontend test suites, frontend production build, API integration checks against configured PostgreSQL, and end-to-end local startup. Review security and database role behavior in the configured runtime.

**Blockers and caveats:** Authentication pepper settings `AUTH_TOKEN_PEPPER` and `PASSWORD_PEPPER` must be supplied as non-example secrets of at least 32 bytes. Token, approval, emergency-stop and audit state are process-local; keep deployment single-worker until shared durable state and lifecycle are implemented and validated. Environment secret lookup is not production secret-manager integration. The user-list endpoint is read-only; admin account creation, role mutation and deletion are not provided. Browser bearer-token storage uses local storage and is not an authorization boundary; backend authorization remains authoritative.

## Phase 3 — Brain, model runtime, memory and knowledge

**Built and committed:** `services/api/modules/brain/` implements deterministic intent classification, confidence thresholds, bounded asynchronous generation, an in-process model registry with priority routing, and safe response orchestration. The OpenAI-compatible HTTP adapter supports local and self-hosted model endpoints; a second self-hosted endpoint is opt-in fallback after primary runtime failure. External AI services are not required. The Brain API exposes model listing and generation, with request validation and safe domain errors. Existing Brain tests cover classifier examples and confidence bounds, routing, local generation, optional fallback, explicit fallback opt-out, input/model/limit rejection, and sanitized failures.

**Validation still outstanding:** Tests and runtime/integration checks were not run for this update. The checked-in test files are not evidence of passing behavior. No live local or self-hosted model endpoint was exercised.

**Boundaries and blockers:** Model registry/configuration is process-local, not durable administrative configuration. Intent confidence is a deterministic heuristic, not factual correctness or answer-quality scoring. Brain generation authorization is not yet integrated with authenticated caller authorization; do not expose it to untrusted callers until server-derived caller context and authorization are enforced and tested. Local/self-hosted endpoint configuration and credentials must be supplied in deployment environment; do not put credentials in source or client requests. External provider fallback remains optional.

## Validation record

Tests and runtime checks have not been run for this update. No database migration/RLS checks, Compose startup, API integration tests, Python test suite, frontend tests or build results are claimed. Record exact commands, environment, outcomes and blockers when validation is performed.

## Next work

Complete Phase 1 database-role/RLS and local Compose verification; run Phase 2 API/security/frontend tests and build; resolve operational gaps above. Integrate authenticated caller authorization into Brain generation as an explicit security-boundary change, with tests, before trusting the endpoint. Then proceed through the approved phase plan; Phase 4 and later implementation is not represented as complete here.
