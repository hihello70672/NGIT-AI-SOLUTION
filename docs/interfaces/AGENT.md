# Personal Agent interface

This contract documents the phase 4 implementation recorded in the repository status; it is not a claim of runtime validation. Authenticated endpoints mount under `/api/v1/agent` only when `NGIT_AGENT_WORKSPACE` explicitly provisions an isolated workspace. The module offers deterministic planning, a tool registry, execution, observations, verification, and process-local task history, using the shared `AuthContext`, `RestrictedActionManager`, and approval engine.

## Safety and execution contract

- The built-in planner converts clear workspace file read/write and HTTP(S) inspection requests into conservative one-step plans. Ambiguous goals fail closed. Any planner must use registered tools and validate handler input.
- Tool handlers return a result containing value, observation, and verification. Failed verification cannot produce task success.
- Filesystem writes, browser navigation, and computer actions are restricted and approval-required under shared policy. Backend authorization is checked against task-step action/resource identifiers before handlers execute. Missing approval pauses before side effects. A distinct reviewer issues exact-action/resource one-time grants; the existing approval workflow consumes them before execution. Rejection, expiry, mismatch, and emergency stop fail closed.
- Task lookup/history is scoped to authenticated owner context. History and approval/security state are process-local; execution is synchronous, not a durable background runner.
- Filesystem paths resolve under the configured workspace; UTF-8 text operations are bounded to 1 MiB. Browser URLs are HTTP(S) only and do not imply a network-fetch implementation. Computer control calls only an explicitly injected adapter; there is no shell/OS implementation.

## REST contract

- `GET /api/v1/agent/tools`
- `POST /api/v1/agent/tasks` with `{"goal":"..."}`; returns accepted task (`202`).
- `GET /api/v1/agent/tasks?limit=50` and `GET /api/v1/agent/tasks/{task_id}`
- `POST /api/v1/agent/approvals?task_id=...` creates a pending grant; an existing reviewer decides through the shared workflow.
- `POST /api/v1/agent/tasks/{task_id}/approve` with `{"approval_id":"..."}`; corresponding reject route rejects a paused task.

All routes require authenticated caller context. Client-supplied owners, policy decisions, arbitrary callables, and resource authority are untrusted. The API does not mount Agent routes when workspace configuration is absent.

## Tests and limits

The status records tests added under `services/api/tests/`; execution remains outstanding. When run, use `PYTHONPATH=. python -m unittest discover -s services/api/tests` from repository root with dependencies installed. Tests should use temporary workspaces and injected fake browser/computer adapters; they should not access external websites or control a desktop. Confirm exact test invocation against the current test README before reporting results.
