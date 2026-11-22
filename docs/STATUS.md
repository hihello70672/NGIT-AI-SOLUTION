# Project status — Phases 1–6

Status reflects committed repository contents on `main`. Test source does not prove tests ran; checked-in implementation does not by itself verify runtime behavior.

## Phase 2 — Authentication, security and users

**Implemented:** Password verification and token lifecycle services; process-local opaque bearer-token authentication; server-derived caller roles; allow-list RBAC/policy authorization and owner checks; exact-scope one-time approvals with separate authorized reviewer; restricted action checks at execution; redacted thread-safe audit events; emergency stop; environment-backed secret lookup. Authenticated API routes provide registration, login/logout, current-user profile read/update, and administrator-only paginated users. The web client now provides sign-in/registration, a responsive user workspace shell, profile management and a backend-connected admin user listing.

**Caveats:** Tokens, approvals, audit and emergency-stop state remain process-local and are not suitable for multi-worker or durable production deployments. Password peppers must be configured through deployment secret management and are never committed. Browser token storage follows the current API contract, not an authorization boundary. Administrator UI visibility is only a convenience; backend authorization is authoritative. Run API and web checks before claiming verification.

## Phase 6 — Administration, billing, rules and service control

**Implemented:** Admin module provides authenticated operations and policy-gated administration. Billing module provides plan definitions, owner-scoped subscriptions, typed provider-independent payment verification, usage metering, idempotency and quota checks, payment history, cancellation/renewal transitions, refund workflow, webhook signature-verification interface and deduplicated event processing. API routes are wired to authenticated server-derived caller context. Migration `0007_billing_lifecycle.sql` declares payment and webhook tables with RLS. Tests cover provider verification, subscription ownership, quotas, webhook verification/deduplication, refunds, cancellation and routes.

**Caveats / remaining work:** Billing and provider run in process memory. The migration is a schema contract only; no database billing adapter is wired and no DB transaction, grant or RLS validation is claimed. Test provider is not a real integration. Durable payment verification/refund execution, provider-key-specific webhook verification/routing, recurring renewal scheduling, operational reconciliation and validated privileges/knowledge/audit grants remain requirements. Permission/rule engine state does not restore after restart; desired service controls lack a deployment executor; approval/emergency state is process-local/single-worker.

## Phase 2 — Web application foundation

**Implemented:** `apps/web` contains a dark responsive interface with green accents and Inter typography; API-backed login/registration, authenticated dashboard navigation, profile settings, Brain chat, Agent tasks and an administrator-only user list. The existing shared API transport continues to use FastAPI `/api/v1` routes. User-management UI displays loading and error states and does not replace backend access checks. UI test source covers auth, registration, dashboard navigation, API-backed chat/Agent, profile and admin UI flows.

**Caveats:** Browser bearer token is kept in local storage to match the current API. The backend's process-local auth/task state limits production deployment. The external Google Fonts import is optional typography enhancement with local sans-serif fallbacks. Frontend test/build commands have not been executed for this update; no passing results are claimed.

## Verification

No tests, builds, migrations, DB checks, Compose lifecycle or runtime checks were executed for this update. No passing results are claimed.
