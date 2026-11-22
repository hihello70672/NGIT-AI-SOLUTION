# Project status — Phases 1–3

This status is based on files present in the reviewed `main` tree. It distinguishes committed implementation from verification; tests have not been run as part of this update, and no passing result is claimed.

## Phase 1 — Foundation, architecture, database, local environment

**Built/committed:** The repository contains the web application under `apps/web`, FastAPI service under `services/api`, PostgreSQL Compose configuration, environment example, architecture/dependency/phase/assignment/shared-protocol documentation, ERD, ordered migrations `0001` through `0004`, reference seed data, schema checks, and migration instructions. Database schema includes user-scoped application records and row-level security.

**Remaining:** Apply migrations to a fresh PostgreSQL 16+ instance and verify migration integrity; review the known integrity warning around `0001_initial_schema.sql`; run schema/RLS checks using a non-owner, non-superuser application role; test cross-user isolation, Compose lifecycle, and API/database integration.

**Risks/blockers:** The migration-integrity warning and live RLS/application-role behavior require verification. Compose is a local PostgreSQL setup, not a production topology.

## Phase 2 — Authentication, security, API, users

**Built/committed:** API configuration, database access with transaction-local caller context, auth/user services, REST routes, request/response schemas, authorization, approval controls, emergency stop, and audit redaction exist. React/TypeScript/Vite web includes sign-in/registration and authenticated user management flows with loading/error/empty states. Test source files exist for API, config, database, and security.

**Runtime limits:** Authentication tokens, approvals, emergency-stop state, and audit events are process-local. Do not assume durable, multi-worker-safe security state; keep deployment to a single worker until persistence and lifecycle are designed and verified. Production secret injection remains an operational decision. `/api/v1/admin/users` is called by the web UI but is not implemented in the current FastAPI app. Brain routes do not yet receive authenticated caller context; do not expose generation to untrusted users without authorization integration.

**Remaining:** Run API/security/config/database and web suites; verify migration compatibility, authentication persistence, transaction-local RLS context and cross-user isolation with PostgreSQL; verify API/web startup and sensitive Brain/tool action authorization. Resolve the admin user-listing contract before relying on it.

## Phase 3 — NGIT Brain and model runtime

**Built/committed:** `services/api/modules/brain` provides typed request/response and runtime interfaces, deterministic offline intent classification with confidence, in-process model registry and priority routing, bounded asynchronous generation, local/self-hosted OpenAI-compatible chat completions, response generation and opt-in self-hosted fallback. Runtime endpoints and optional credentials are configured only by server environment; external AI APIs are not required. Evaluation test sources cover classifier examples, confidence bounds, registry ordering, generation, routing, fallback behavior, and safe failures.

**Runtime limits:** Registry/configuration are process-local. No endpoint configured means generation is unavailable while deterministic Brain interfaces remain importable. Brain API authentication is not yet integrated. Intent confidence measures classifier certainty, not answer correctness or factual quality.

**Remaining:** Run Brain and API evaluation suites; validate configured local/self-hosted endpoints and timeout behavior in an appropriate environment; review authorization before exposing generation to untrusted callers; decide durable model configuration as future integration work.

## Validation record

Tests have not been run for this status update. Checked-in tests are source coverage, not evidence of passing execution. API/security/web, database migrations/RLS, Compose, model endpoint connectivity, and integration outcomes remain unverified. Record exact commands and environment when these checks are run; do not report them as passing before then.
