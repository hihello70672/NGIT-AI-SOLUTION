# Shared interface and protocol conventions

These conventions guide coordination; they do not prove every endpoint or schema exists. Review domain contracts before extending them. FastAPI OpenAPI is the machine-readable API contract when routes are implemented. Cross-cutting contract or status-catalog changes require Chief Architect approval.

## Module/service boundaries

- Expose domain operations through typed service contracts. HTTP handlers validate/parse inputs, obtain authenticated caller context, call services, serialize responses, and map errors.
- User-scoped operations receive explicit server-derived caller context. Client-supplied IDs, roles, permissions, or approvals do not establish ownership or authority.
- A module owns its persistence. Cross-module operations use published contracts rather than private implementation imports or direct writes to another module’s tables.
- Validate trust-boundary inputs, including provider callbacks, imported content, browser/tool results, and administration.
- Long-running work reports accepted submission, observable status, result/failure, and timeout behavior. Runner technology and delivery guarantees are open; do not claim durability without implementation and verification.

## REST and errors

- Versioned REST routes use `/api/v1`; lowercase plural resource names and lowercase kebab-case compound path segments. Use consistent HTTP methods and typed request/response schemas.
- JSON fields use `snake_case`; identifiers are opaque strings; timestamps use UTC RFC 3339. Document enum values and units.
- Distinguish validation, authorization, not-found, conflict, rate-limit, and server failures with suitable HTTP status codes.
- Errors should be safe and actionable, with a stable code and user-facing message; optional validation details/correlation ID are permitted. Never expose credentials, private prompts, stack traces, provider internals, or another user’s data.
- Existing endpoint contracts take precedence. A new universal error envelope or altered status catalog needs Chief Architect approval; follow the applicable existing interface until approved.

## WebSocket and event conventions

Use WebSockets only for justified streaming or bidirectional features. If adopted, messages are versioned JSON envelopes, for example:

```json
{
  "version": 1,
  "event_id": "opaque-id",
  "type": "domain.event_name",
  "occurred_at": "UTC RFC 3339 timestamp",
  "correlation_id": "opaque-id",
  "data": {}
}
```

Scope events to the authenticated user and authorized resource. Define authentication, event ordering, disconnect/reconnect, replay, retries, and delivery semantics before production streaming. This convention does not establish an event bus or durable delivery. Do not put credentials or unnecessary personal data in events.

## Data, isolation, naming, and security

- PostgreSQL is the system of record. Enforce user ownership in service queries and test cross-user isolation. Validate RLS with a non-owner, non-superuser role; policy and context decisions remain subject to verification.
- Audit sensitive and administrative operations without logging tokens, credentials, private prompts, or unnecessary personal data.
- Use stable machine-readable enum values. Represent money as currency plus integer minor units, never floating point.
- Python/database identifiers use `snake_case`; Python types use `PascalCase`; API paths are lowercase. Document conversions at boundaries.
- Secrets enter through environment/configuration or an approved secret interface. Never commit secrets or expose them to browser code.
- Sensitive tool actions require backend authorization and any policy-required approval immediately before execution. UI confirmation is not authorization.
- Preserve owner/caller context through tasks. Define idempotency, retry, cancellation, dead-letter, and delivery semantics before claiming reliable background execution.

## Open transport/tooling decisions

Frontend tooling details beyond the existing React/TypeScript/Vite application; ORM/migrations; authentication/session format; RLS policy; vector search; model runtime; task runner; WebSocket auth/delivery; media storage; and secrets management remain open as documented in [architecture](../ARCHITECTURE.md#decisions-still-open). Do not silently select them.
