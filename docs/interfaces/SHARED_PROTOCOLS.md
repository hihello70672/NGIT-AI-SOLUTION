# Shared interface and protocol conventions

These conventions guide coordination; they do not prove every endpoint or schema exists. FastAPI OpenAPI is the machine-readable API contract once routes are implemented. Cross-cutting contract or status-catalog changes require Chief Architect approval. Inspect current routes and schemas before extending; existing client contracts take precedence over proposed universal conventions.

## Module/service boundaries

- Expose domain operations through typed service contracts. HTTP handlers validate and parse inputs, obtain authenticated caller context, invoke services, serialize responses, and map errors.
- User-scoped operations receive explicit **server-derived** caller context. Client-supplied IDs, roles, permissions, or approvals do not establish ownership or authority.
- A module owns its persistence and migrations. Cross-module operations use published contracts, never private implementation imports or direct writes to another module’s tables.
- Validate all trust-boundary inputs, including provider callbacks, imported content, browser/tool results, and administration.
- Long-running work reports accepted submission, observable status, result/failure, and timeout behavior. Runner technology and delivery guarantees remain open; do not claim durability without implementation and verification.

## REST and errors

- REST is the default. Follow existing routes and schemas; preserve compatibility. Versioning, universal error envelope, and JSON casing must be reviewed against current API before standardization.
- Validate at the API boundary; authorization is enforced by backend services, never by the UI.
- Use appropriate HTTP semantics to distinguish validation, authentication, authorization, not-found, conflict, rate-limit, and server failures.
- Errors should be safe and actionable, with stable machine-readable code and user-facing message; include a request/correlation identifier where the existing interface supports it. Do not expose credentials, tokens, private prompts, stack traces, provider internals, or another user’s data.
- Do not silently change existing status codes or endpoint contracts. Chief Architect approval is required for a shared error-envelope/catalog change.

## Caller context, data, and security

- Caller identity and privileges are derived from authenticated server context. Never trust user IDs, roles, permissions, or approvals supplied only by clients.
- PostgreSQL is authoritative. Enforce ownership in service queries, test cross-user isolation, and validate RLS with a non-owner, non-superuser application role. Policy/context choices remain open until verified.
- Sensitive actions pass backend authorization and required policy/approval checks immediately before execution. UI confirmation is not authorization. Audit outcomes without logging tokens, credentials, private prompts, or unnecessary personal data.
- Keep all provider credentials and payment secrets server-side. Never commit secrets.
- Use Python `snake_case`, TypeScript `camelCase`, SQL `snake_case` for new identifiers unless current repository conventions require compatibility.
- Represent money as currency plus integer minor units, not floating point. Use stable enum values and UTC RFC 3339 timestamps at external boundaries; document units and conversions.

## Events, tasks, and WebSockets

Use WebSockets only for justified streaming or bidirectional features. If adopted, define authentication, owner/resource scope, event ordering, disconnect/reconnect, replay, retry, and delivery behavior before relying on them. An illustrative JSON envelope may carry version, opaque event ID, event type, UTC occurrence time, correlation ID, and data; it does not establish an event bus or durable delivery.

Task/event envelopes identify type, correlation, owner context where applicable, timestamp, and payload. Validate payloads and make failure states explicit. Before claiming reliable background execution, define idempotency, retry, cancellation, dead-letter, delivery semantics, persistence, and caller-context propagation. Keep credentials and unnecessary personal data out of events.

## Open implementation choices

ORM/migration tooling, authentication/session format, RLS policy, vector search, model runtime, task runner, WebSocket authentication/delivery, media storage, and secret-management implementation remain open as recorded in [architecture](../ARCHITECTURE.md#decisions-still-open). Do not silently select a technology or imply behavior not implemented.
