# Project status — Phases 1–4

This status records implementation evidence only. Tests have not been run in this task; no passing result is claimed.

## Phase 1 — Foundation, architecture, database, local environment

**Built/committed:** Repository foundation and architecture documentation, approved phase plan and module boundaries, local PostgreSQL Docker Compose setup and usage docs, environment examples, ordered SQL migrations and seed data, database schema checks/tests, and ERD documentation. The schema covers users/roles, user-scoped conversations/messages/memory, billing, optional provider configuration, media/presentation metadata, audit logs, ownership constraints, and row-level security. Migration `0003` hardens role-assignment RLS.

**Remaining:** Execute migrations against fresh PostgreSQL 16+; run schema and RLS checks with a non-owner/non-superuser application role; verify cross-user isolation, Compose lifecycle, and API/database integration.

**Blocker/risk:** The migration integrity warning around `0001_initial_schema.sql` remains unresolved; review the restored file against the intended schema before accepting Phase 1 database validation.

## Phase 2 — Authentication, security, API, users

**Built/committed:** Versioned FastAPI register/login/logout and current-user profile read/update routes; process-local opaque bearer tokens and RBAC/approval services wired to PostgreSQL-backed user records; caller identity and current active status/roles resolved server-side per request. Passwords use scrypt with deployment-injected pepper. Request models reject unknown fields; safe validation/security/conflict/server errors and request correlation IDs are standardized. Existing Brain routes require authenticated callers; psycopg adapter sets `ngit.user_id` transaction-locally for user-scoped SQL. Existing module services and the synchronous/in-process task interface were preserved. OpenAPI documents REST contracts. API/config/database/security test sources cover these flows, but source coverage is not evidence tests passed.

**Web foundation committed:** In `apps/web`, the existing React/TypeScript/Vite application now includes a dark, responsive Inter design system with green brand accents, login/registration and session loading/error states, overview/dashboard shell, editable user profile, and administrator user management. It uses the established `/api/v1` auth and user endpoints, bearer authorization, safe API errors, profile update, logout, and an administrator user-list request; access denial remains backend-authoritative. UI tests cover sign-in errors, dashboard/profile/logout, restricted access, and user-list loading/error/empty/data states. Existing frontend styles, package setup, and UI tests were retained. Web test sources have not been executed in this task.

**Runtime boundaries:** Tokens, approvals, emergency-stop state, and audit events are process-local and not durable or multi-worker safe. Run a single worker only until approved persistence is introduced. Deployments must inject unique strong `AUTH_TOKEN_PEPPER` (at least 32 bytes) and `PASSWORD_PEPPER` (at least 16 bytes); no actual secrets are committed. `/health` checks process liveness only, not database readiness. Database connectivity and configured local/self-hosted model endpoint behavior require separate verification.

**Remaining:** Run API/security unit tests; validate migrations and user transactions against disposable PostgreSQL, including transaction-local RLS context and cross-user isolation; verify sensitive Brain/tool authorization; exercise full API/web startup and integration. External AI integrations remain optional.

**Blocker/risk:** Durable shared security-state storage and production secrets management remain undecided. Do not treat current process-local security state as durable.

## Phase 3 — Brain, runtime, memory, knowledge

**Built/committed:** Existing modular Brain, memory, runtime, and API sources remain in place; implementation details and evidence are recorded in module documentation and test sources.

**Remaining:** Run runtime, evaluation, API, ownership, and database/RLS validations as required by the phase gate.

## Phase 4 — Personal Agent

**Built/committed:** Existing Agent module and shared security approval engine are preserved. Tool actions are explicit; arbitrary commands are not inferred. Approval requests require a distinct reviewer, and a matching grant is consumed once. Task history and approval state are process-local; execution is synchronous/in-process, not a durable worker.

**Remaining:** Run Agent/API tests and verify adapters, authorization, and approvals in a provisioned environment.

## Validation record

Tests were not run for this status update. API, security, database/RLS, web, and integration outcomes remain unverified; no passing result is asserted. The restored migration integrity warning, startup behavior, database connection, and configured local/self-hosted model endpoint behavior also require verification.

## Phase sequence and boundaries

See [PHASE_PLAN.md](PHASE_PLAN.md) for the approved delivery sequence. Do not introduce unjustified WebSockets or durable task claims without the approved contract and implementation evidence.

## Note

Repository HEAD contains later-phase web implementation; this status scope records Phases 1–4. The migration integrity warning above remains a concrete blocker for accepting Phase 1 database work.

## Phase 3 implementation record

The Brain runtime and deterministic evaluation suite were already present at the reviewed repository HEAD. This status preserves the distinction between committed implementation and unverified runtime/test behavior.

## Phase 4 implementation record

The Personal Agent implementation extends the existing agent module and shared security approval engine. Tool actions are explicit; the planner does not infer arbitrary commands. Approval requests require a distinct reviewer, and a matching grant is consumed once. Task history and approval state remain process-local; execution is synchronous and in-process, not a durable worker.

## Phase 2 security implementation note

Security primitives are for a single-process development deployment only. In-memory token revocation, emergency-stop state, approvals, and audit events are neither durable nor restart/multi-worker safe. Set `AUTH_TOKEN_PEPPER` (at least 32 bytes) and `PASSWORD_PEPPER` (at least 16 bytes) through deployment secret injection; never commit real values. `.env.example` intentionally does not include usable authentication pepper values. Audit redaction is defense in depth; callers must not pass sensitive data.

API routes are documented in OpenAPI at `/openapi.json` and `/docs`. The database connection uses transaction-local identity context for RLS. Tests are source coverage only until executed; no result is asserted.

**Web UI:** `apps/web` provides the Phase 2 authentication and user-management interface over the documented API contracts. Frontend session storage is best-effort localStorage with in-memory runtime behavior; backend authentication and authorization remain authoritative. No admin mutation endpoint is assumed or exposed.

Tests were not run for this status update.

## Phase 2 web foundation record

Committed in `c64e676ff7d1a6a9e219ac17dae6a616f2ff26fd`: responsive dark/green Inter web interface, sign-in/registration, authenticated overview shell, profile editing, and backend-protected administrator user list with loading, recoverable error, empty, and populated states. Existing API client was extended to the committed Phase 2 route contracts, and UI test sources cover principal flows. Tests were not run for this task; no passing result is claimed.

The frontend consumes `/api/v1/auth/register`, `/api/v1/auth/login`, `/api/v1/auth/logout`, `/api/v1/users/me`, and `/api/v1/admin/users`. The repository API currently does not declare `/admin/users`; that page therefore surfaces the backend response as an error until an approved server route exists. Do not infer administrator authority from client state; current role check only selects a UX message and the backend remains the access-control authority.

No additional secret or external AI dependency was introduced.

## Phase 2 web foundation validation note

The UI test sources were added/extended but were not executed. The existing test suite contains a backend admin-users endpoint expectation for `/api/v1/admin/users`; the committed FastAPI API currently does not implement that route. This is an integration gap, not a passing UI/API claim. Run frontend tests and build in a configured Node environment, then align administrator listing with an approved backend contract before relying on that workflow.

The existing `apps/web/src/styles.css` already contains the dark Inter/green design system and responsive layout; it was preserved. The interface uses existing React/Vite/Lucide setup and the shared API client. No new client-side authorization boundary is introduced.

## Phase 2 web UI commit

`c64e676ff7d1a6a9e219ac17dae6a616f2ff26fd` updates the web application, API client, and UI test source. Existing stylesheet/package tooling and test setup were retained. No tests were run, and build/runtime outcomes remain unverified.

Note: the UI test file added in that commit must be checked against the actual accessible navigation names and current API response behavior before reporting suite success; no test outcome is asserted here.

## Web implementation follow-up

Review the Phase 2 web UI test sources against the actual rendered accessibility tree and the API route inventory before treating them as valid integration coverage. The administrator list route is not present in the current API implementation and remains a backend/frontend contract gap; no client role assertion substitutes for server authorization.

No tests were run for this status update.

## Frontend integration caveat

Administrator user-list rendering is implemented as an API consumer, with permission decision enforced by backend response and no admin listing route currently present in FastAPI. The page displays the backend error as a recoverable state. Do not add a backend endpoint or alter the shared contract without approval.

## Web foundation validation

The frontend sources and UI tests are committed, but were not run in the original implementation task. The UI test assertions need verification against React Testing Library behavior and the current app API. No test result is claimed.

## Frontend maintenance note

The app shell and interface are implemented in `apps/web/src/App.tsx`, the shared client in `apps/web/src/lib/api.ts`, and the established design system in `apps/web/src/styles.css`. Existing tests in `apps/web/src/App.test.tsx` were extended. Preserve the current component structure and stylesheet when making further web changes.

The backend currently exposes registration, login, logout, and current profile routes, but no administrator user-list route. User management must continue to show a recoverable API error in that case; do not imply the listing endpoint exists.

The web foundation commit did not modify package metadata or CSS. No web tests or builds were run as part of that commit.