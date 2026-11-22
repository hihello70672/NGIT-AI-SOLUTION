# Project status — Phases 1–6

Status reflects committed repository content on `main`. Test source is not evidence of executed test outcomes.

## Phase 2 — Authentication, security and users

**Implemented:** Password verification and token lifecycle services; process-local opaque bearer-token authentication; server-derived caller roles; allow-list RBAC/policy authorization with owner checks; exact-scope one-time approvals with separate authorized reviewer; restricted action checks at execution; redacted thread-safe audit events; emergency stop; environment-backed secret lookup. Security regression tests cover policy immutability and ownership, reviewer separation, approval scope/expiry/concurrency, stop-state behavior, audit redaction and immutability, secret-name validation and token expiry.

**Caveats:** Tokens, approvals, audit and emergency-stop state are process-local and are not suitable for multi-worker or durable production deployments. The configured peppers must come from deployment secret management and are never committed. Existing API defaults consequently require `AUTH_TOKEN_PEPPER` to be configured. Run the API tests and database/RLS checks before claiming verification.

## Phase 6 — Administration, billing, rules and service control

**Implemented:** Admin module provides authenticated operations and policy-gated administration. Billing module provides plan definitions, owner-scoped subscriptions, typed provider-independent payment verification, usage metering, idempotency and quota checks, payment history, cancellation and renewal transitions, refund workflow, webhook signature verification interface and deduplicated event processing. API routes are wired and derive caller identity from authenticated server context. Migration `0007_billing_lifecycle.sql` declares payment and webhook tables with RLS. Tests cover provider verification, subscription ownership, quotas, webhook verification/deduplication, refunds, cancellation and routes.

**Caveats / remaining work:** Billing state and provider run in process memory. Migration is a schema contract only and no DB billing adapter is wired; database transactions, grants and RLS validation remain. Test provider is not a real integration. Durable payment verification/refund execution, provider-key-specific webhook verification/routing, recurring renewal scheduling and operational reconciliation are required before production. Permission/rule-engine state does not restore after restart; desired service controls lack deployment executor; approval/emergency state is process-local/single-worker. Validate provider, knowledge and audit grants.

## Verification

No tests, builds, migrations, DB checks, Compose lifecycle or runtime checks were executed for this update. No passing results are claimed.
