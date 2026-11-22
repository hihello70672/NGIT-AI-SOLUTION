"""Deterministic Personal Agent planner and approval-gated tool execution."""
from __future__ import annotations
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from threading import RLock
from typing import Any, Callable, Mapping
from urllib.parse import urlparse
from uuid import uuid4
from services.api.security import AuthContext, RestrictedActionManager, SecurityError

class AgentError(ValueError):
    """Safe machine-readable agent failure."""
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code, self.message = code, message

@dataclass(frozen=True)
class PlannedStep:
    tool_name: str
    arguments: Mapping[str, Any]
    description: str

@dataclass(frozen=True)
class AgentPlan:
    task_id: str
    owner_id: str
    goal: str
    steps: tuple[PlannedStep, ...]
    created_at: str

@dataclass(frozen=True)
class ToolResult:
    value: Any
    observation: str
    verified: bool

@dataclass
class TaskRecord:
    task_id: str
    owner_id: str
    goal: str
    state: str
    created_at: str
    updated_at: str
    plan: list[dict[str, Any]] = field(default_factory=list)
    observations: list[dict[str, Any]] = field(default_factory=list)
    result: Any = None
    error: str | None = None
    pending_approval_id: str | None = None

@dataclass(frozen=True)
class ToolDefinition:
    name: str
    description: str
    sensitive: bool
    handler: Callable[[Mapping[str, Any]], ToolResult]

class ToolRegistry:
    """Explicit allowlist for agent capabilities."""
    def __init__(self) -> None:
        self._tools: dict[str, ToolDefinition] = {}

    def register(self, definition: ToolDefinition) -> None:
        if not re.fullmatch(r"[a-z][a-z0-9_.-]{1,63}", definition.name):
            raise ValueError("invalid tool name")
        if definition.name in self._tools:
            raise ValueError("tool name already registered")
        self._tools[definition.name] = definition

    def get(self, name: str) -> ToolDefinition:
        try:
            return self._tools[name]
        except KeyError as exc:
            raise AgentError("tool_not_found", "Requested tool is not available") from exc

    def list(self) -> list[dict[str, Any]]:
        return [{"name": t.name, "description": t.description, "sensitive": t.sensitive}
                for t in sorted(self._tools.values(), key=lambda item: item.name)]

class BrowserInterface:
    """Adapter-based browser boundary; navigation is sensitive."""
    def __init__(self, reader: Callable[[str], str] | None = None, navigator: Callable[[str], Any] | None = None) -> None:
        self.reader = reader or (lambda url: f"Browser adapter unavailable for {urlparse(url).netloc}")
        self.navigator = navigator

    @staticmethod
    def _url(value: Any) -> str:
        if not isinstance(value, str) or len(value) > 2048:
            raise AgentError("invalid_arguments", "A valid HTTP(S) URL is required")
        parsed = urlparse(value)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.username or parsed.password:
            raise AgentError("invalid_arguments", "A valid HTTP(S) URL is required")
        return value

    def inspect(self, args: Mapping[str, Any]) -> ToolResult:
        value = self.reader(self._url(args.get("url")))
        if not isinstance(value, str):
            raise AgentError("tool_failed", "Browser adapter returned an invalid observation")
        return ToolResult(value[:20000], "Browser page inspected", True)

    def navigate(self, args: Mapping[str, Any]) -> ToolResult:
        url = self._url(args.get("url"))
        if self.navigator is None:
            raise AgentError("tool_unavailable", "Browser navigation adapter is not configured")
        return ToolResult(self.navigator(url), "Browser navigation completed", True)

class FilesystemInterface:
    """Workspace-sandboxed UTF-8 text access with bounded writes."""
    def __init__(self, root: str | Path) -> None:
        self.root = Path(root).expanduser().resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def resolve(self, value: Any) -> Path:
        if not isinstance(value, str) or not value or len(value) > 1024:
            raise AgentError("invalid_arguments", "A relative filesystem path is required")
        path = (self.root / value).resolve()
        if path != self.root and self.root not in path.parents:
            raise AgentError("path_forbidden", "Filesystem path escapes the configured workspace")
        return path

    def read(self, args: Mapping[str, Any]) -> ToolResult:
        path = self.resolve(args.get("path"))
        try:
            if not path.is_file() or path.stat().st_size > 1_000_000:
                raise AgentError("invalid_arguments", "File is missing or exceeds the read limit")
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError as exc:
            raise AgentError("invalid_arguments", "Only UTF-8 text files can be read") from exc
        return ToolResult(text, f"Read {path.relative_to(self.root)}", True)

    def write(self, args: Mapping[str, Any]) -> ToolResult:
        path = self.resolve(args.get("path"))
        content = args.get("content")
        if not isinstance(content, str) or len(content.encode("utf-8")) > 1_000_000:
            raise AgentError("invalid_arguments", "Text content is required and must be at most 1 MB")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return ToolResult({"path": str(path.relative_to(self.root)), "bytes": len(content.encode("utf-8"))},
                          "File written", path.read_text(encoding="utf-8") == content)

class ComputerControlInterface:
    """No shell or OS control is implicit; explicit adapter only."""
    def __init__(self, adapter: Callable[[str, Mapping[str, Any]], Any] | None = None) -> None:
        self.adapter = adapter

    def perform(self, args: Mapping[str, Any]) -> ToolResult:
        action = args.get("action")
        if action not in {"screenshot", "click", "type", "keypress"}:
            raise AgentError("invalid_arguments", "Unsupported computer action")
        if self.adapter is None:
            raise AgentError("tool_unavailable", "Computer-control adapter is not configured")
        return ToolResult(self.adapter(action, args), f"Computer action {action} completed", True)

class AgentPlanner:
    """Conservative planner for explicit, inspectable requests."""
    def plan(self, owner_id: str, goal: str) -> AgentPlan:
        if not owner_id or not isinstance(goal, str) or not goal.strip() or len(goal) > 4000:
            raise AgentError("invalid_goal", "A non-empty goal of at most 4000 characters is required")
        text = goal.strip()
        steps: list[PlannedStep] = []
        match = re.fullmatch(r"(?:read|show)\s+(?:file\s+)?(.+)", text, re.I)
        if match:
            steps.append(PlannedStep("filesystem.read", {"path": match.group(1).strip()}, "Read a workspace file"))
        else:
            match = re.fullmatch(r"(?:write|create)\s+(?:file\s+)?([^\n]+?)\s+with\s+content:\s*([\s\S]*)", text, re.I)
            if match:
                steps.append(PlannedStep("filesystem.write", {"path": match.group(1).strip(), "content": match.group(2)}, "Write a workspace file"))
            else:
                match = re.fullmatch(r"(?:inspect|open)\s+(https?://\S+)", text, re.I)
                if match:
                    steps.append(PlannedStep("browser.inspect", {"url": match.group(1)}, "Inspect a web page"))
                else:
                    raise AgentError("plan_unavailable", "Could not safely turn this goal into an explicit tool plan")
        return AgentPlan(str(uuid4()), owner_id, text, tuple(steps), datetime.now(timezone.utc).isoformat())

class AgentService:
    def __init__(self, tools: ToolRegistry, permissions: RestrictedActionManager, planner: AgentPlanner | None = None) -> None:
        self.tools, self.permissions = tools, permissions
        self.planner = planner or AgentPlanner()
        self._records: dict[str, TaskRecord] = {}
        self._plans: dict[str, AgentPlan] = {}
        self._lock = RLock()

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    def submit(self, context: AuthContext, goal: str) -> TaskRecord:
        plan = self.planner.plan(context.user_id, goal)
        now = self._now()
        record = TaskRecord(plan.task_id, context.user_id, plan.goal, "accepted", now, now,
            plan=[{"tool_name": s.tool_name, "arguments": dict(s.arguments), "description": s.description} for s in plan.steps])
        with self._lock:
            self._records[record.task_id], self._plans[record.task_id] = record, plan
        return self.execute(context, record.task_id)

    def _complete_step(self, record: TaskRecord, step: PlannedStep, index: int) -> bool:
        try:
            result = self.tools.get(step.tool_name).handler(step.arguments)
            record.observations.append({"step": index, "tool_name": step.tool_name,
                "observation": result.observation, "verified": result.verified})
            if not result.verified:
                raise AgentError("verification_failed", "Tool result could not be verified")
            record.result = result.value
            return True
        except AgentError as exc:
            record.state, record.error = "failed", exc.code
        except Exception:
            record.state, record.error = "failed", "tool_failed"
        return False

    def execute(self, context: AuthContext, task_id: str, approval_id: str | None = None) -> TaskRecord:
        with self._lock:
            record, plan = self._records.get(task_id), self._plans.get(task_id)
            if record is None or plan is None or record.owner_id != context.user_id:
                raise AgentError("task_not_found", "Task was not found")
            if record.state in {"succeeded", "failed", "rejected"}:
                return record
            if record.state == "running":
                raise AgentError("task_running", "Task is already running")
            record.state, record.updated_at = "running", self._now()
        results = []
        try:
            for index, step in enumerate(plan.steps):
                tool = self.tools.get(step.tool_name)
                resource_id, action = f"{task_id}:{index}", f"agent.tool.{tool.name}"
                if tool.sensitive:
                    try:
                        self.permissions.authorize(context, action, resource_id, approval_id=approval_id)
                    except SecurityError as exc:
                        if exc.code == "approval_required":
                            with self._lock:
                                record.state, record.updated_at = "awaiting_approval", self._now()
                                record.observations.append({"step": index, "state": "approval_required", "action": action, "resource_id": resource_id})
                            return record
                        raise
                result = tool.handler(step.arguments)
                record.observations.append({"step": index, "tool_name": tool.name,
                    "observation": result.observation, "verified": result.verified})
                if not result.verified:
                    raise AgentError("verification_failed", "Tool result could not be verified")
                results.append(result.value)
            record.result = results[0] if len(results) == 1 else results
            record.state, record.error = "succeeded", None
        except (AgentError, SecurityError) as exc:
            record.state, record.error = "failed", exc.code
        except Exception:
            record.state, record.error = "failed", "tool_failed"
        record.updated_at = self._now()
        return record

    def approve_and_resume(self, context: AuthContext, task_id: str, approval_id: str) -> TaskRecord:
        with self._lock:
            record, plan = self._records.get(task_id), self._plans.get(task_id)
            if record is None or plan is None or record.owner_id != context.user_id:
                raise AgentError("task_not_found", "Task was not found")
            if record.state != "awaiting_approval":
                raise AgentError("invalid_task_state", "Task is not awaiting approval")
            pending = next((o for o in record.observations if o.get("state") == "approval_required"), None)
            if pending is None:
                raise AgentError("invalid_task_state", "No pending action requires approval")
            action, resource_id, index = pending["action"], pending["resource_id"], pending["step"]
        try:
            self.permissions.authorize(context, action, resource_id, approval_id=approval_id)
        except SecurityError as exc:
            record.state, record.error, record.updated_at = "failed", exc.code, self._now()
            return record
        with self._lock:
            record.observations = [o for o in record.observations if o.get("state") != "approval_required"]
            record.pending_approval_id, record.state = None, "running"
        if len(plan.steps) != 1 or index != 0:
            record.state, record.error, record.updated_at = "failed", "resume_not_supported", self._now()
            return record
        # The shared grant was consumed before handler invocation. Do not call
        # authorize again: that would reject a correctly consumed one-time grant.
        if self._complete_step(record, plan.steps[index], index):
            record.state, record.error = "succeeded", None
        record.updated_at = self._now()
        return record

    def reject(self, context: AuthContext, task_id: str) -> TaskRecord:
        with self._lock:
            record = self._records.get(task_id)
            if record is None or record.owner_id != context.user_id:
                raise AgentError("task_not_found", "Task was not found")
            if record.state != "awaiting_approval":
                raise AgentError("invalid_task_state", "Task is not awaiting approval")
            record.state, record.error, record.updated_at = "rejected", "approval_rejected", self._now()
            return record

    def get(self, context: AuthContext, task_id: str) -> TaskRecord:
        with self._lock:
            record = self._records.get(task_id)
            if record is None or record.owner_id != context.user_id:
                raise AgentError("task_not_found", "Task was not found")
            return record

    def history(self, context: AuthContext, limit: int = 50) -> list[TaskRecord]:
        if not 1 <= limit <= 100:
            raise AgentError("invalid_limit", "Limit must be between 1 and 100")
        with self._lock:
            return sorted((r for r in self._records.values() if r.owner_id == context.user_id), key=lambda r: r.created_at, reverse=True)[:limit]

def build_agent(tools: ToolRegistry, permissions: RestrictedActionManager, workspace: str | Path,
                browser: BrowserInterface | None = None, computer: ComputerControlInterface | None = None) -> AgentService:
    browser, computer = browser or BrowserInterface(), computer or ComputerControlInterface()
    fs = FilesystemInterface(workspace)
    tools.register(ToolDefinition("browser.inspect", "Read-only HTTP(S) page inspection", False, browser.inspect))
    tools.register(ToolDefinition("browser.navigate", "Approval-gated HTTP(S) browser navigation", True, browser.navigate))
    tools.register(ToolDefinition("filesystem.read", "Read UTF-8 text in the agent workspace", False, fs.read))
    tools.register(ToolDefinition("filesystem.write", "Approval-gated workspace text write", True, fs.write))
    tools.register(ToolDefinition("computer.perform", "Approval-gated computer action via configured adapter", True, computer.perform))
    return AgentService(tools, permissions)

def public_record(record: TaskRecord) -> dict[str, Any]:
    return {"task_id": record.task_id, "goal": record.goal, "state": record.state, "created_at": record.created_at,
        "updated_at": record.updated_at, "plan": record.plan, "observations": record.observations,
        "result": record.result, "error": record.error, "pending_approval_id": record.pending_approval_id}
