# Personal Agent interface

This contract guides the Agent boundary; it is not a claim that every capability is complete or runtime-validated. Inspect `services/api/modules/agent/` and [shared protocols](SHARED_PROTOCOLS.md) before changes. Shared contract/boundary changes require Chief Architect review.

## Responsibility and dependencies

The Agent owns planning, registered-tool contracts, execution coordination, observation and verification. It consumes server-derived caller context and shared security/policy/approval and task contracts. Tools are typed, bounded capabilities—not authorization authorities.

## Contract requirements

- Validate typed submission/status/result/owner/correlation/failure schemas at API boundaries.
- Task history/detail is owner-scoped. Never treat a client-supplied owner as authority.
- Specify idempotency, retries, cancellation and durable lifecycle before claiming reliable or multi-worker execution.
- Treat tool input/output as untrusted; impose size/time limits and sanitize errors.
- Do not mark success if an action failed, approval was rejected/expired/mismatched, or verification failed. Report observation/verification evidence.
- Sensitive effects run shared policy and scoped approval checks immediately before execution and emit audit results. A requester cannot approve their own sensitive action where separation is required.

## Adapter safety

Browser navigation requires approved origins and network-level SSRF defenses: DNS/IP restrictions, redirect handling, response limits and protections against local/private/metadata networks. URL syntax validation is insufficient. Filesystem workspace checks are not an OS sandbox and do not eliminate symlink/race attacks; use deployment isolation for untrusted files. Computer control must be an explicitly injected, constrained adapter; no arbitrary OS control is implied. External AI remains optional.

## Current operational caveat

Status reports task/security state as process-local. Operate one worker until shared durable state and task lifecycle semantics are designed and validated. Test source presence is not test execution evidence. See [project status](../STATUS.md).
