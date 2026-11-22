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

**Built and committed:** The Brain services include deterministic intent classification, bounded generation, local/self-hosted runtime routing and safe orchestration. The private Memory services implement authenticated user-owned conversation creation/listing, ordered messages, typed short-/long-term memory records, lexical retrieval, optional owner-scoped vector candidate reranking, chunked knowledge ingestion with provenance, and exact URL-origin allowlist verification without fetching remote URLs. Existing schema tables, composite ownership constraints, transaction-local PostgreSQL RLS context, authenticated REST routes and privacy-focused unit/API tests are used. Vector embeddings/indexing remain optional adapters because the approved schema has no embedding column or vector extension; search filters returned vector hits through the authenticated user's memory corpus before returning them. External AI APIs are not required.

**Validation still outstanding:** Tests and database/runtime integration checks have not been run for this update. Checked-in test files are source coverage only and do not prove PostgreSQL RLS behavior. No live vector provider or remote source content was exercised.

**Boundaries and blockers:** Database connection grants and a non-owner, non-superuser application role must be configured and RLS verified before deployment. The vector adapter requires a trusted embedding function and candidate loader that honors owner scope; it is optional and does not persist embeddings in the current schema. Source allowlisting verifies URL origin only; it neither fetches nor authenticates source content. Knowledge text is caller-provided and untrusted. Brain caller authorization and process-local model/security state retain the caveats described above.

## Validation record

Tests and runtime checks have not been run for this update. No database migration/RLS checks, Compose startup, API integration tests, Python test suite, frontend tests or build results are claimed. Record exact commands, environment, outcomes and blockers when validation is performed.

## Next work

Complete Phase 1 database-role/RLS and local Compose verification; run Phase 2 API/security/frontend tests and build; verify Phase 3 privacy with real PostgreSQL RLS and configured role; address Brain authorization before exposing it to untrusted callers. Then proceed through the approved phase plan; Phase 4 and later implementation is not represented as complete here.
