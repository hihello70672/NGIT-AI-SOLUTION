# Project status — Phases 1–2

Status is based on files present in the reviewed `main` tree. Checked-in tests are source coverage only. Tests and runtime checks have not been run for this update; no passing result is claimed.

## Phase 1 — Foundation, architecture, database and local environment

**Built and committed:** Repository layout includes `apps/web`, `services/api`, `infra/docker`, database migrations/tests, and architecture documentation. Local PostgreSQL Compose configuration and root `.env.example` are present. Five ordered SQL migrations (`0001`–`0005`) define the isolated `ngit` schema, users, roles, conversations/messages, typed memories, billing, optional provider metadata, media/video/presentation metadata, audit logs, indexes and forced RLS. Seed data and transactional SQL integration checks cover selected tenant isolation and constraints. Architecture, dependency, phase, assignment, ERD and shared-interface documentation are present.

**Remaining:** Apply migrations to a fresh PostgreSQL 16+ instance; validate schema, indexes and seed data; run isolation checks using a provisioned application role that is neither superuser nor table owner; verify migration/application grants; validate Compose lifecycle and local startup.

**Blockers/caveats:** Migrations run lexically as a privileged migration principal. Tenant checks must not run as superuser or table owner. Provision a separate non-owner/non-superuser application role without `BYPASSRLS` and grant only required privileges. API code must set `ngit.user_id` transaction-locally only from authenticated server context, never client input. Provider metadata stores opaque credential references, not secrets. External AI is optional. Database and Compose behavior remain unverified.

## Phase 2 — Authentication, security, API, users and web client

**Built and committed:** FastAPI configuration, request IDs, safe errors, authentication/user services, REST schemas/routes, server-enforced authorization and transaction-local database caller context are present. Security primitives include expiring/revocable bearer tokens, policy/ownership checks, approval/emergency-stop controls, redacted audit events and environment secret lookup. The React/TypeScript/Vite client includes sign-in/registration, authenticated dashboard shell, profile settings and administrator user listing; responsive design system; and a shared API client with loading, empty, error/retry, expired-session and backend access-denied handling. User listing is read-only; authorization remains backend-enforced. UI test sources cover authentication errors, registration mode, profile update/logout, admin denial, user-list loading/error/retry/empty/populated states and expired sessions. Backend, security and API test sources are also present.

**Remaining:** Run backend and frontend test suites, frontend production build, PostgreSQL-backed API integration, and end-to-end local startup; review security and database-role behavior.

**Blockers/caveats:** Example peppers must be replaced with local non-example secrets. Token, approval, emergency-stop and audit state are process-local; use a single worker until shared durable state exists. Environment lookup is not production secret management. Browser local-storage bearer tokens are not an authorization boundary. Runtime checks and suites have not been run.

## Validation record

No tests or runtime checks have been run for this update. This includes Python/API, SQL migration/RLS, Compose, frontend tests/build and live integration checks. Checked-in test files are not evidence of execution or passing results.

## Next work

Run the documented API and web suites and resolve failures. Complete PostgreSQL migration/RLS checks with a non-owner role, verify grants and lifecycle, and validate Compose and end-to-end local startup. Review security boundaries and plan durable shared state before multi-worker use. Record exact commands, environment and outcomes after performing validation.
