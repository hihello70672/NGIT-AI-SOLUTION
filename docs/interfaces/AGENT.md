# Personal Agent interface

Authenticated endpoints mount under `/api/v1/agent` only when `NGIT_AGENT_WORKSPACE` explicitly provisions an isolated workspace. The module provides deterministic planning, an explicit tool registry, execution, observations, verification and process-local task history. It uses the established `AuthContext`, `RestrictedActionManager` and `ApprovalEngine`.

## Safety and execution contract

- The built-in planner only converts clear workspace file read/write and HTTP(S) inspection requests into one-step plans; ambiguous goals fail closed. Any future planner must still use registered tools and validate handler input.
- Tool handlers return `ToolResult(value, observation, verified)`. A failed verification cannot produce a successful task state.
- `filesystem.write`, `browser.navigate` and `computer.perform` are sensitive. The API registers `agent.tool.<tool-name>` policies as restricted and approval-required in the shared policy engine. Authorization is checked against task-step resource IDs before handlers execute. A missing approval pauses the task without side effect. A distinct reviewer must issue the exact-action/resource one-time approval through the existing workflow; authorization consumes it before execution. Rejection, expiry, mismatch and emergency stop fail closed.
- Authenticated owner context scopes task lookup and history. History is in-memory and not durable across process restart; execution is synchronous, not a durable background runner.
- Filesystem access resolves paths under the configured workspace; UTF-8 text operations are bounded to 1 MB. Browser URLs are restricted to HTTP(S), with no implicit network-fetch implementation. Computer interface only calls an explicitly injected adapter and has no shell/OS implementation.

## REST

- `GET /api/v1/agent/tools`
- `POST /api/v1/agent/tasks` with `{ "goal": "..." }` (202)
- `GET /api/v1/agent/tasks?limit=50`; `GET /api/v1/agent/tasks/{task_id}`
- `POST /api/v1/agent/approvals?task_id=...` creates a pending grant in the shared engine; an existing reviewer decides it using the shared approval workflow.
- `POST /api/v1/agent/tasks/{task_id}/approve` with `{ "approval_id": "..." }`; `POST .../reject` rejects a paused task.

All endpoints require authenticated caller context. Client-supplied owners, policy decisions, arbitrary callables and resource authorization are not trusted. The API does not mount agent routes when workspace configuration is absent.

## Tests

Run `PYTHONPATH=. python -m unittest discover -s services/api/tests` from the repository root. Agent tests use temporary workspaces and injected fake browser/computer adapters; they do not access external websites or control a desktop.
