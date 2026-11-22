# Shared interface and protocol conventions

These are coordination contracts for implementation. They do not claim endpoints or schemas currently exist. FastAPI's generated OpenAPI document is the initial machine-readable API contract once routes are implemented.

## Module/service boundary

- Expose domain operations through typed service interfaces; HTTP handlers remain thin (parse request, obtain auth context, serialize response, map errors).
- User-scoped operations receive explicit caller/user context. Do not trust client-supplied IDs as ownership evidence.
- Modules own their persistence. Cross-module use goes through published service contracts, never private implementation or direct table writes.
- Validate at API boundaries and whenever internal/background inputs cross trust boundaries.
- Background-task interfaces report submission acceptance, status, and failure; runner technology is unselected. Long/external operations expose explicit states, actionable errors, and timeout/status behavior.

## REST and error conventions

- Version REST APIs at `/api/v1`.
- Use plural lowercase resource names; use lowercase kebab-case only for compound path segments; use consistent HTTP methods.
- JSON fields use `snake_case`; identifiers are opaque strings; timestamps are UTC RFC 3339.
- Distinguish validation, authorization, not-found, conflict, rate-limit, and server failures with appropriate HTTP status codes.
- Error envelope:

```json
{
  "error": {
    "code": "stable_machine_readable_code",
    "message": "Safe message for the caller",
    "request_id": "opaque-request-id",
    "details": {}
  }
}
```

`details` must not expose secrets, internal prompts, stack traces, or another user's data. Define stable error codes alongside each endpoint as it is added.

## WebSocket/event conventions

Use WebSockets only when interactive/streamed updates justify them. Each message is a versioned JSON envelope:

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

Events must be scoped to the authenticated user and authorized resource. Specify concrete event names and payloads with the feature. WebSocket authentication, reconnection, and delivery guarantees must be decided before production streaming implementation.

## Data, security, and naming

- PostgreSQL is the system of record. User-owned records require enforceable ownership and authenticated user-scoped queries; test that users cannot access each other's data.
- Audit security-sensitive and administrative operations. Avoid credentials, tokens, private prompts, and unnecessary personal data in logs.
- Use stable machine-readable enum values. Money is currency plus integer minor units, never floating point.
- Python modules/functions and database identifiers use `snake_case`; Python types use `PascalCase`; API paths are lowercase.
- Secrets enter through environment/configuration or an approved secret-management interface. Never commit them or expose them to browser code.
- Sensitive tool actions require backend authorization and any policy-required approval. UI confirmation alone is insufficient.
- The web client consumes public API behavior and does not enforce authorization, billing, or user isolation.

## Open transport/tool decisions

Frontend framework/toolchain, ORM/migrations, authentication/session format, row-level security, vector search, model runtime, task runner, WebSocket auth/delivery semantics, artifact storage, and secret-management requirements remain open as recorded in `docs/ARCHITECTURE.md`. Do not silently select them.
