# Shared protocols and service contracts

This is the shared starting point for module work. Inspect existing implementation/contracts before changes. Chief Architect review is required for changes to shared contracts, dependencies or boundaries. Preserve existing routes and schemas unless an approved compatibility-aware change is made.

## Contract ownership

- A module publishes typed request/result contracts and documents validation, authorization context, persistence ownership, dependencies and failure behavior.
- Consumers invoke published capabilities only. Do not import private implementation details, write another module's tables, or create duplicate shared services.
- PostgreSQL is authoritative for persisted application state. Each module/service owns its tables and migrations.
- API versioning, exact error envelope and shared serialized casing remain open until reconciled with current routes/schemas.

## Caller context and authorization

- Authenticated API boundaries derive caller identity/roles from verified server-side authentication. Never trust client-supplied user IDs, roles, permissions or approvals.
- Services pass typed server-derived caller context to authorized operations. Owner-scoped queries enforce ownership at the service boundary.
- Set PostgreSQL `ngit.user_id` transaction-locally from authenticated server context where required; never from request payload data.
- Where RLS applies, test with a non-owner, non-superuser application role without `BYPASSRLS`. Include cross-user isolation checks. RLS is defense in depth, not a substitute for service authorization.
- Run shared policy/approval checks immediately before sensitive execution. Fail closed on missing/failed authorization, approval, verification or emergency-stop state; record relevant results through audit contracts.
- Do not claim multi-worker durability from process-local state. Until shared durable state and lifecycle are designed/validated, observe documented single-worker caveats.

## API validation, errors and untrusted data

- REST is default. WebSockets require a justified streaming/bidirectional use case and approved authentication, authorization, message, reconnect and close/error behavior.
- Validate all API boundary inputs; bound size, time and resource use. Return stable machine-readable codes, safe user-facing messages and request/correlation identifiers.
- Never expose secrets, internal traces, prompts or another user's data in logs/responses.
- Provider callbacks, imported knowledge, browser/tool outputs and administrative input are untrusted and must be validated/bounded before use.
- Credentials and provider secrets remain server-side. Environment lookup is not a production secret-management solution.
- Browser adapters require SSRF/network defenses (DNS/IP restrictions, redirects, response limits and approved origins); URL syntax checks alone are insufficient. Filesystem checks are not an OS sandbox. Computer-control requires an explicitly injected constrained adapter.

## Tasks, events and persistence

- Long-running task contracts define task status/result/failure, owner context, correlation, idempotency, retry, cancellation and failure behavior before claims of reliability/durability.
- Event/task envelopes identify type, correlation, applicable owner context, timestamp and payload; consumers validate payload and handle failure states.
- Event transport, delivery guarantees and schema versioning remain open. Do not introduce a broker or standardize incompatible envelopes without architecture review.
- PostgreSQL transactions have explicit boundaries. Cross-module data access uses public contracts. Verify tenant isolation as a non-owner/non-superuser without `BYPASSRLS`.

## Naming and compatibility

Use existing repository conventions where compatibility requires them. New Python identifiers use `snake_case`, TypeScript uses `camelCase`, SQL uses `snake_case`. Reconcile JSON casing with existing API models before enforcing a new shared convention. Update the appropriate `docs/interfaces/` contract before or alongside breaking changes.

## Open decisions

Auth/session and durable-token approach; database grants/RLS deployment policy; persistent approval/emergency/audit state; task runner/scheduling; WebSocket auth/reconnect; event transport/schema/delivery; API version/error envelope/JSON casing; vector/embedding persistence; secret management; and media/artifact storage remain open as documented in [architecture](../ARCHITECTURE.md#6-decisions). Do not silently choose divergent module implementations.
