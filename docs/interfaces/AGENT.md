# Personal Agent interface

The authenticated agent module is mounted below `/api/v1/agent` only when the API is configured with an explicitly provisioned `NGIT_AGENT_WORKSPACE`. It owns task planning, tool registry, execution, observations, verification and in-process task history. It uses the existing shared `AuthContext`, `RestrictedActionManager` and `ApprovalEngine`; no competing policy implementation is introduced.

## Contracts and safety

- `AgentPlanner.plan(owner_id, goal)` returns a bounded, inspectable plan. The deterministic built-in supports clear workspace file reads/writes and HTTP(S) page inspection; ambiguous tasks are rejected. Tool registry membership and handler validation remain mandatory for any planner adapter.
- `ToolRegistry` is an explicit capability allowlist. Handlers return `ToolResult(value, observation, verified)`; failed verification cannot report task success.
- Sensitive capability actions use `agent.tool.<tool-name>` and a task-step resource ID. The API registers filesystem write, browser navigation and computer action policies as restricted and approval-required in the shared policy engine. Missing approval pauses the task before the handler runs. A different authorized reviewer must decide the shared one-time grant; it must match exact actor/action/resource and is consumed before the side effect. Rejection, expiry, mismatch and emergency stop fail closed.
- Task reads/history are scoped to authenticated owner. History is in-process and not durable across restarts; long-running/background execution is not claimed.
- Filesystem paths are resolved under the configured workspace; UTF-8 text reads and writes are limited to 1 MB. Browser adapter accepts HTTP(S) URLs only, does not fetch arbitrary content by default, and has no implicit browser dependency. Computer control has no shell/OS implementation and requires explicit adapter injection.

## REST

- `GET /api/v1/agent/tools`
- `POST /api/v1/agent/tasks` with `{ "goal": "..." }` (202)
- `GET /api/v1/agent/tasks?limit=50`; `GET /api/v1/agent/tasks/{task_id}`
- `POST /api/v1/agent/approvals?task_id=...` creates a pending grant in the existing approval engine. An existing authorized reviewer decides it using the shared workflow.
- `POST /api/v1/agent/tasks/{task_id}/approve` with `{ "approval_id": "..." }` resumes a pending task; `/reject` rejects it.

All routes require authenticated caller context. Client-supplied owner, policy decisions, arbitrary tool callables or resource authorization are not accepted. Agent REST routes are not exposed without workspace configuration.

## Tests

Run `PYTHONPATH=. python -m unittest discover -s services/api/tests` from repository root. Agent tests use temporary workspaces and injected fake browser/computer adapters; they do not visit real websites or control a desktop.
