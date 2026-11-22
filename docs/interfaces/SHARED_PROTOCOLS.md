# Shared protocols and service contracts

These protocols are the approved shared starting point for modules. Inspect this document and current code before extending an interface. Changes to shared contracts, dependency rules, or module boundaries require Chief Architect review. Preserve existing routes and schemas unless an approved, compatibility-aware change is made.

## Contract ownership

- A module publishes typed request/result contracts and documents validation, authorization context, persistence ownership, dependencies, and failure behavior.
- Consumers call published capabilities only. Do not import private implementation details, write another module's tables, or create duplicate shared services.
- PostgreSQL is authoritative persisted application state. Each service/module owns its tables and migrations.
- Shared JSON casing, API versioning, and exact error-envelope conventions remain open until reconciled with existing routes and schemas.

## Caller context and authorization

- Authenticated API boundaries derive caller identity and roles from verified server-side authentication. Never trust client-supplied user IDs, roles, permissions, or approvals.
- Services pass typed server-derived caller context to authorized operations. User-scoped queries enforce ownership at the service boundary.
- Set PostgreSQL `ngit.user_id` transaction-locally from authenticated server context where required; do not accept that value from request payloads.
- Where RLS applies, validate it as a non-owner, non-superuser application role without `BYPASSRLS`. Tests must include cross-user isolation.
- Use shared policy/approval checks immediately before sensitive execution when required; fail closed on missing authorization, approval, verification, or emergency-stop state. Record relevant outcomes through audit contracts.

## API validation, errors, and untrusted data

- REST is the default. WebSockets require a justified streaming or bidirectional use case. Authentication and reconnect semantics are open until approved.
- Validate all API-boundary inputs and enforce authorization in backend services. Frontend checks are usability only, never a security boundary.
- Errors should expose stable machine-readable codes, user-safe messages, and request/correlation identifiers. Never expose secrets, internal stack traces, prompts, or other users' data.
- Treat provider callbacks, imported knowledge, browser/tool output, and administrative input as untrusted; validate and bound them before use.
- Credentials and provider secrets remain server-side. Environment lookup alone is not production secret management.

## Tasks, events, and persistence

- Long-running task contracts define status and result, owner context, correlation, idempotency, retry, cancellation, and failure behavior before durability/reliability claims.
- An event/task envelope identifies type, correlation, owner context where applicable, timestamp, and payload. Consumers validate payloads and handle failures.
- Event transport and exact event/task schema remain open; do not standardize or introduce a broker without architecture review.
- Do not infer durable multi-worker execution from process-local state. Follow documented single-worker caveats until shared durable state is designed and validated.

## Naming and compatibility

Use repository conventions where compatibility requires them. New Python identifiers use `snake_case`, TypeScript uses `camelCase`, and SQL uses `snake_case`. Reconcile cross-language JSON casing with existing API models before setting a convention.

## Security and isolation

- Keep secrets, tokens, prompts, stack traces, and cross-user data out of logs and responses.
- Verify owner isolation in service queries and with tests. Database RLS is defense in depth, not a substitute for service authorization.
- Browser adapters require SSRF/network controls, including allowed origins, DNS/IP restrictions, redirect handling, and response limits. URL syntax checks alone are insufficient.
- Filesystem path checks are not an OS sandbox; use deployment isolation for untrusted access. Computer control requires an explicitly injected, constrained adapter.
- Sensitive actions are rejected if authorization, approval, verification, or emergency-stop checks fail.

## Open decisions

ORM/migration tooling; authentication/session format; durable security and task state; RLS context and database-role grants; event transport; exact event/error/JSON contracts; WebSocket auth/reconnect; local model distribution; vector/embedding persistence; media storage; payment provider; external adapters and secret management; and production operations remain open unless existing implementation or later architecture review settles them.
