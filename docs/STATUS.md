# Project status — Phases 1–2

Status is based on files present in the reviewed `main` tree. Checked-in tests are source coverage only. Tests and runtime checks have not been run for this update; no passing result is claimed.

## Phase 1 — Foundation, architecture, database, local environment

**Built and committed:** The repository layout includes `apps/web`, `services/api`, `infra/docker`, database migrations and tests, and architecture documentation. Local PostgreSQL Compose configuration (`compose.yaml`) and a root environment example (`.env.example`) are present. Documentation covers architecture, dependencies, the phase plan, assignments, shared protocols, and Brain/Memory/Agent interfaces. The database work includes the ERD, four ordered migrations (`0001`–`0004`), reference seed data, schema checks and migration instructions. The schema covers user-scoped conversations/messages and memories with row-level security, billing, provider metadata, media/video/presentation metadata, audit logs, and indexes.

**Remaining:** Apply migrations to a fresh PostgreSQL 16+ instance; check migration integrity, schema constraints, seeds and indexes; exercise RLS and tenant isolation using an explicitly provisioned application role; and validate Compose/local startup.

**Blockers and caveats:** The SQL test runner's migration role needs schema/table creation privileges and does not itself establish the non-owner application role needed to prove forced RLS. Provision a separate non-owner, non-superuser role without `BYPASSRLS` for tenant-path checks. Migration `0001` creates schema `ngit` but does not grant application schema/table privileges; configure grants out of band. The migration ledger is in `public`, separate from application tables in `ngit`; verify ownership and grants separately. No database or Compose checks have been run.

## Phase 2 — Authentication, security, API, users and web client

**Built and committed:** The FastAPI application includes validated configuration, request IDs, safe error handling, authentication and user services, REST routes/schemas, server-enforced authorization and transaction-local database caller context. Security primitives include expiring/revocable bearer tokens, role and ownership policies, approval and emergency-stop controls, redacted audit events and environment-backed secret lookup. The React/TypeScript/Vite client includes sign-in/registration, authenticated dashboard, profile settings, admin user-list flow and the shared API client, with checked-in API, security, configuration and UI regression tests.

**Remaining:** Execute backend and frontend test suites, frontend production build, API integration checks against configured PostgreSQL, and end-to-end local startup. Review security and database role behavior in the configured runtime.

**Blockers and caveats:** Authentication pepper settings `AUTH_TOKEN_PEPPER` and `PASSWORD_PEPPER` must be supplied as non-example secrets of at least 32 bytes. Token, approval, emergency-stop and audit state are process-local; keep deployment single-worker until shared durable state and lifecycle are implemented and validated. Environment secret lookup is not a production secret-manager integration. The user-list endpoint is read-only; account creation by admins, role mutation and deletion are not provided. Browser bearer-token storage uses local storage and is not an authorization boundary; backend authorization remains authoritative.

## Validation record

Tests and runtime checks have not been run for this update. No database migrations/RLS checks, Compose startup, API integration tests, Python test suite, frontend tests or build results are claimed. Record exact commands, environment, outcomes and blockers when validation is performed.

## Next work

Complete Phase 1 database-role/RLS and local Compose verification, run Phase 2 API/security/frontend tests and build, resolve operational gaps above, then proceed through the approved phase plan. Later phases and integrations are outside this status update.
