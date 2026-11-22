# Shared interface and protocol conventions

These are coordination conventions for implementation, not proof that every described endpoint or schema exists. FastAPI's generated OpenAPI document is the machine-readable API contract once routes are implemented. Review the existing domain contracts before extending them; cross-cutting shared-contract changes require Chief Architect approval.

## Module and service boundaries

- Expose domain operations through typed service interfaces. HTTP handlers remain thin: parse/validate input, obtain authenticated caller context, invoke services, serialize responses, and map errors.
- User-scoped operations receive explicit server-derived caller context. Client-supplied IDs are not ownership evidence.
- Modules own their persistence. Cross-module operations use published service contracts, never private implementation or direct table writes.
- Validate at API boundaries and whenever internal/background inputs cross trust boundaries.
- Background-task contracts must make submission acceptance, status, and failure observable. Runner technology and delivery guarantees are not selected. Long-running/external operations require explicit timeout and status/failure behavior.

## REST and errors

- Version REST APIs under `/api/v1`.
- Use lowercase plural resource names and lowercase kebab-case only for compound path segments; use consistent HTTP methods.
- JSON fields use `snake_case`; identifiers are opaque strings; timestamps are UTC RFC 3339.
- Distinguish validation, authorization, not-found, conflict, rate-limit, and server failures using suitable HTTP status codes.
- Error responses must be safe and actionable, and must not expose secrets, internal prompts, stack traces, or another user's data. Define stable error codes alongside each endpoint.
- The shared error envelope shown in legacy/domain interface material is not a universally approved API-wide schema. Any new or changed common envelope/status catalog requires Chief Architect approval; follow the applicable existing endpoint contract until approved.

## WebSocket and event conventions

Use WebSockets only when interactive/streamed updates justify them. If adopted, each message is a versioned JSON envelope:

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

Events are scoped to the authenticated user and authorized resource. Specify event names and payloads with the feature. Authentication, reconnect, and delivery guarantees must be decided before production streaming; this convention does not establish an event bus.

## Data, security, and naming

- PostgreSQL is the system of record. User-owned records require enforceable ownership and authenticated user-scoped queries; test that users cannot access one another's data. RLS behavior and whether to use it in addition to service checks require validation/decision.
- Audit security-sensitive and administrative operations. Avoid credentials, tokens, private prompts, and unnecessary personal data in logs.
- Use stable machine-readable enum values. Money is currency plus integer minor units, never floating point.
- Python modules/functions and database identifiers use `snake_case`; Python types use `PascalCase`; API paths are lowercase.
- Secrets enter through environment/configuration or an approved secret-management interface. Never commit them or expose them to browser code.
- Sensitive tool actions require backend authorization and any policy-required approval. UI confirmation alone is insufficient.
- The web client consumes public API behavior and does not enforce authorization, billing, or user isolation.

## Open transport/tooling decisions

Frontend framework/toolchain details, ORM/migrations, authentication/session format, RLS policy, vector search, model runtime, task runner, WebSocket auth/delivery, artifact storage, and secret-management requirements remain open as recorded in [`docs/ARCHITECTURE.md`](../ARCHITECTURE.md). Do not silently select them.
