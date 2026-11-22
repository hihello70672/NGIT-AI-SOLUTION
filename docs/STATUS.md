# Project status — Phases 1–2

This status is based on files present in the reviewed `main` tree. It records committed implementation separately from verification; tests have not been run for this status update, and no passing result is claimed.

## Phase 1 — Foundation, architecture, database, local environment

**Built/committed:** The repository contains the web application under `apps/web`, the FastAPI service under `services/api`, documentation under `docs`, local PostgreSQL Compose configuration (`compose.yaml`), `.env.example`, and Docker setup guidance (`infra/docker/README.md`). Architecture, dependency map, phase plan, agent assignments, shared protocols, and ERD are documented. The database tree contains ordered migrations `0001_initial_schema.sql` through `0004_complete_domain_schema.sql`, reference seed data, schema checks, and migration/test instructions. The SQL schema documents user/role records, user-scoped application data, domain tables, ownership, and row-level security.

**Remaining:** Apply migrations to a fresh PostgreSQL 16+ instance and verify migration integrity; run database schema/RLS checks with a non-owner, non-superuser application role; test cross-user isolation; and exercise the Compose lifecycle and API/database integration. Review migration `0001_initial_schema.sql` and its known integrity warning before accepting Phase 1 validation.

**Blockers/risks:** The unresolved migration-integrity warning around `0001_initial_schema.sql` blocks acceptance of the database foundation until reviewed. RLS behavior and the production role/context arrangement also require live verification. Compose currently provides local PostgreSQL; it does not establish a production topology.

## Phase 2 — Authentication, security, API, users

**Built/committed:** The API tree includes environment configuration, pooled PostgreSQL access with transaction-local RLS caller context, user/auth services, FastAPI application routes, request/response schemas, and security services. The committed API supports registration, login, logout, current-user profile retrieval/update, bearer-token authentication, server-side account/role checks, password hashing, authorization and ownership checks, approval controls, emergency stop, and audit redaction. Request validation and safe error handling are present. Backend tests cover API, config, database context, and security behavior. The existing React/TypeScript/Vite web application has sign-in/registration, an authenticated overview, profile editing, and user management UI with loading, error, and empty states; its API client uses `/api/v1`. Relevant test sources are committed but are not evidence of passing tests.

**Runtime limitations:** Tokens, approvals, emergency-stop state, and audit events are process-local, not durable or safe for multiple workers/restarts; keep deployment to a single worker until persistence is designed and verified. Configure unique strong `AUTH_TOKEN_PEPPER` (at least 32 bytes) and `PASSWORD_PEPPER` (at least 16 bytes) using secret injection. No real credentials are committed. `/health` is a liveness check, not a database-readiness check.

**Remaining:** Run API/security/config/database and web tests; validate migrations and authenticated user transactions against disposable PostgreSQL, including transaction-local RLS and cross-user isolation; exercise sensitive Brain/tool authorization; and verify full API/web startup and database integration. The frontend administrator list calls `/api/v1/admin/users`, but that route is absent from the current FastAPI application; align the UI with an approved backend contract before relying on that workflow.

**Blockers/risks:** Process-local security state prevents durable or multi-worker deployment assumptions. Production secret management and persistence for security/audit state are not settled. The missing admin user-list API endpoint is a concrete frontend/backend integration gap. Database and model-runtime connectivity are not verified.

## Validation record

Tests have not been run for this status update. The checked-in test files are source coverage only; API, security, web, migration, RLS, Compose lifecycle, and integration outcomes remain unverified. Do not report these checks as passing until run and recorded with exact commands and environment.
