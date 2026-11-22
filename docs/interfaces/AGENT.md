# Personal Agent interface

This document describes the Agent module boundary and security requirements. It is a contract guide, not a claim that every proposed capability is implemented or runtime-validated. Current implementation and caveats are tracked in [project status](../STATUS.md). Inspect the current Agent code and [shared protocols](SHARED_PROTOCOLS.md) before changes. Changes to shared contracts require Chief Architect review.

## Responsibility and dependencies

Personal Agent owns planning, tool registration, execution coordination, observation, and verification. It consumes server-derived caller context and shared security/policy/approval capabilities. Tools are explicitly registered, typed, bounded, and invoked through published contracts; a tool adapter is not an authorization authority.

## Contract requirements

- Task submission, status, result, owner, correlation, and failure behavior are typed and validated at the API boundary.
- Task history and detail are owner-scoped. Never use request-supplied owner identity as authority.
- Define idempotency, retry, cancellation, and durable lifecycle before claiming reliability or multi-worker support.
- Tool inputs and outputs are untrusted; apply size/time limits and sanitize safe error responses.
- Observation and verification must not mark a task successful when an action failed, approval was rejected/expired/mismatched, or verification failed.
- Sensitive actions invoke shared policy and approval checks immediately before execution when required, bind approval to exact scope, and emit relevant audit results. The requester cannot approve their own sensitive operation when separation is required.

## Adapter safety

- Browser navigation requires approved origin and network protections: DNS/IP restrictions, redirects, response limits, and protection against access to local/private/metadata networks. URL syntax validation alone does not establish SSRF safety.
- Filesystem workspace checks are not an OS sandbox and do not eliminate symlink/race attacks. Use an explicitly isolated deployment boundary for untrusted files.
- Computer-control implementations are injected adapters. They must be constrained and separately authorized; this contract does not provide arbitrary OS control.
- External AI is optional and is not required for the deterministic Agent path.

## Current operational caveat

The status record describes process-local task/security state. Operate a single worker until shared durable state and lifecycle semantics are designed and validated. Do not claim test or runtime success from checked-in test sources.
