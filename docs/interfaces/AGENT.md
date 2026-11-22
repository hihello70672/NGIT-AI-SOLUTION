# Personal Agent interface

The agent is an authenticated module under `/api/v1/agent`. It owns planning, an explicit tool registry, execution, observations, verification and in-process task history. `AgentService` accepts a shared `AuthContext` and a shared `RestrictedActionManager`; it does not implement competing authorization or approval logic.

## Contracts

- `AgentPlanner.plan(owner_id, goal) -> AgentPlan` returns an inspectable bounded plan. The built-in planner handles explicit file read/write and HTTP(S) inspection intents; ambiguous goals are rejected. Future planner adapters must keep the same validation boundary.
- `ToolRegistry` only exposes registered capabilities. Tool handlers accept validated argument mappings and return `ToolResult(value, observation, verified)`.
- `AgentService.submit` creates a task and executes safe steps. Sensitive write/navigation/computer actions are checked via `RestrictedActionManager.authorize` with `agent.tool.<tool-name>` and a task-step resource ID. A missing approval leaves the task in `awaiting_approval` without executing the side effect. A one-time shared approval must match actor, action and resource and be issued by a distinct reviewer. Approval rejection or mismatch fails closed.
- Observations and verification are stored with the task. Failed verification never reports success. `get` and `history` are owner-scoped.
- `FilesystemInterface` resolves every path under its configured workspace and caps text reads/writes at 1 MB. `BrowserInterface` accepts only HTTP(S), has no implicit browser dependency, and defaults to safe read-only observation. `ComputerControlInterface` has no shell/OS implementation and requires an explicit adapter.
- Task history is in-process and is not durable across API process restarts. The shared task contract does not select a runner; durable execution is deferred until approved.

## REST

- `GET /agent/tools`
- `POST /agent/tasks` with `{ "goal": "..." }` (202)
- `GET /agent/tasks?limit=50`, `GET /agent/tasks/{task_id}`
- `POST /agent/approvals?task_id=...` requests a grant through the injected shared approval engine; a separate reviewer must decide it through the existing approval workflow.
- `POST /agent/tasks/{task_id}/approve` with `{ "approval_id": "..." }` resumes a pending task.
- `POST /agent/tasks/{task_id}/reject`

All routes use authenticated caller context. Client-provided owner IDs, tool names, policy decisions and arbitrary callables are never trusted. Agent endpoints are only mounted when the API supplies an isolated workspace configuration and the shared approval engine; no implicit host filesystem or computer access is enabled.

## Verification

Run `PYTHONPATH=. python -m unittest discover -s services/api/tests` from repository root. Agent tests use temporary workspaces and fake browser/computer adapters; they do not access real websites or control a desktop.
