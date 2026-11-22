# Personal Agent interface

This contract describes the Phase 4 implementation. It is not a claim of runtime validation. Authenticated endpoints mount under `/api/v1/agent` only when `NGIT_AGENT_WORKSPACE` explicitly configures an isolated workspace. Requests use the server-derived shared `AuthContext`; client-supplied owner IDs, policy decisions and arbitrary callables are not trusted.

## Planning and execution

The deterministic planner accepts clear single-step workspace file read/write and HTTP(S) inspection goals. Ambiguous goals fail closed. Plans reference registered tools only. Tool handlers return a value, observation and verification result; false verification or handler failure never yields success. Task history is owner-scoped and process-local. Execution is synchronous, not a durable background runner.

The filesystem adapter limits UTF-8 text operations to 1 MiB and resolves paths under the configured root. This containment is not an OS-level sandbox and does not replace deployment filesystem isolation or symlink/race hardening. Browser inspection and navigation are adapter-based; navigation is sensitive. URL syntax validation is not an SSRF/network safety policy. A configured browser adapter must enforce allowed origins, DNS/IP restrictions, redirect and response-size limits. Computer control has no built-in OS/shell implementation and invokes only an explicitly injected adapter.

## Approval and sensitive actions

Filesystem writes, browser navigation and computer control use shared `RestrictedActionManager`, policy engine, emergency stop and approval engine. A sensitive action is authorized with an exact action string and task-step resource ID before its handler can execute. Missing approval pauses the task. Approval grants are exact-scope and single-use; denial, expiry, mismatch, emergency stop and rejection fail closed. The task owner may request a grant but cannot decide it: a distinct authenticated reviewer must make the decision through the shared approval engine. The user must resume the task with the approved grant. Never bypass the engine or treat a grant request as approval.

## REST routes

- `GET /api/v1/agent/tools`
- `POST /api/v1/agent/tasks` with `{"goal":"..."}` returns accepted task state.
- `GET /api/v1/agent/tasks?limit=50` and `GET /api/v1/agent/tasks/{task_id}` return owner-scoped history/task details.
- `POST /api/v1/agent/tasks/{task_id}/approve` requests a pending exact-scope grant; it does not approve it.
- `POST /api/v1/agent/approvals/{approval_id}/decision` with `{"approved":true}` is for an authenticated distinct reviewer and delegates to the shared approval engine.
- `POST /api/v1/agent/tasks/{task_id}/resume` with `{"approval_id":"..."}` consumes the approved grant and executes the paused step.
- `POST /api/v1/agent/tasks/{task_id}/reject` rejects a task awaiting approval without executing its side effect.

## Validation and operational limits

Agent unit and API tests are checked in under `services/api/tests/`; tests/runtime checks have not been executed for this implementation update. Run `PYTHONPATH=. python -m pytest services/api/tests` from repository root with documented dependencies. Task history and approval/security state are process-local. Keep a single worker until durable shared state and lifecycle are designed and validated. External AI APIs are optional and are not used by this deterministic agent engine.
